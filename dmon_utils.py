from __future__ import print_function
from mpi4py import MPI
import time, thread, sys, string

def logger(*args, **kwargs):
	s = string.join([str(x) for x in args])

	c = ''
	e = ''
	if kwargs.get('color'):
		if kwargs.get('color') == 'green':
			c = '\033[92m'
		elif kwargs.get('color') == 'yellow':
			c = '\033[93m'
		else:
			c = '\033[94m'
		e = '\033[0m'
	rank = MPI.COMM_WORLD.Get_rank()
	sys.stdout.write(c + '(%d @ %f)' % (rank, time.time()) + s + e + '\n')

class ConditionVar:
	def __init__(self, var_id, monitor):
		self.var_id = var_id
		self.monitor = monitor

	def wait(self):
		self.monitor.handle_pending_requests()
		logger('leaves critical section, state %d' % self.monitor._state_stamp, self.monitor.fields(), color='green')
		self.monitor._waiting_on = self
		self.monitor._state = MonitorState.WAITING_FOR_SIGNAL
		self.monitor._lock.acquire() # suspend until signal is received
		self.monitor.lock()

	def signal(self):
		signal = Message(MessageType.SIGNAL,
			var_id = self.var_id,
			monitor_id = self.monitor.id)
		signal.broadcast()

class Monitor:
	def __init__(self, id):
		self.id = id
		self._state_stamp = 0
		self._lock = thread.allocate_lock()
		self._waiting_on = None
		self._state = MonitorState.IDLE
		self._pending_requests = []
		self._last_request = None
		self._replies_count = 0
		thread.start_new_thread(self._listener_routine, ())

	# Release the critical section
	def handle_pending_requests(self):
		self._state_stamp += 1
		field_state = self.fields()
		for r in self._pending_requests:
			self.send_reply(r)
		self._pending_requests = []

	def send_reply(self, recvmsg):
		field_state = self.fields()
		reply = Message(
			MessageType.RA_REPLY,
			monitor_id = self.id,
			request_timestamp = recvmsg.payload.get('timestamp'),
			state_stamp = self._state_stamp,
			field_state = field_state)
		reply.send_to(recvmsg.sender)

	def send_request(self):
		request = Message(
			MessageType.RA_REQUEST,
			timestamp = time.time(),
			monitor_id = self.id)
		logger('send request (tst %f)' % request.payload.get('timestamp'))
		request.broadcast()
		self._last_request = request
		self._replies_count = 0

	def handle_reply(self, recvmsg):
		if recvmsg.payload.get('request_timestamp') == self._last_request.payload.get('timestamp'):
			logger('received reply from %d' % recvmsg.sender, color='blue')
			if recvmsg.payload.get('monitor_id') == self.id:
				recvstamp = recvmsg.payload.get('state_stamp')
				if recvstamp > self._state_stamp:
					self._state_stamp = recvstamp
					field_state = recvmsg.payload.get('field_state')
					for k in field_state:
						setattr(self, k, field_state[k])
					logger('updating - payload:', recvmsg.payload)
				self._replies_count += 1
				if self._replies_count >= MPI.COMM_WORLD.size - 1:
					self._state = MonitorState.IN_CRITICAL_SECTION
					self._replies_count = 0
					if self._lock.locked():
						self._lock.release()

	def handle_signal(self, recvmsg):
		if recvmsg.payload.get('var_id') == self._waiting_on.var_id and \
		   recvmsg.payload.get('monitor_id') == self.id:
			self.send_request()
			self._lock.release()
			self._state = MonitorState.WAITING_FOR_REPLIES

	def _listener_routine(self):
		self._lock.acquire()
		while True:
			recvmsg = Message.wait_for()

			if self._state == MonitorState.IDLE:
				if recvmsg.msg_type == MessageType.RA_REQUEST:
					self.send_reply(recvmsg)
				
			elif self._state == MonitorState.WAITING_FOR_REPLIES:
				if recvmsg.msg_type == MessageType.RA_REQUEST:
					if self._last_request == None or \
					   recvmsg.payload['timestamp'] < self._last_request.payload['timestamp'] or \
					   recvmsg.payload.get('monitor_id') != self.id:
						self.send_reply(recvmsg)
					else:
						self._pending_requests += [recvmsg]
				elif recvmsg.msg_type == MessageType.RA_REPLY:
					logger('receive reply from %d (req %f)' % (recvmsg.sender, recvmsg.payload.get('request_timestamp')))
					self.handle_reply(recvmsg)

			elif self._state == MonitorState.WAITING_FOR_SIGNAL:
				if recvmsg.msg_type == MessageType.SIGNAL:
					self.handle_signal(recvmsg)
				elif recvmsg.msg_type == MessageType.RA_REQUEST:
					# not in critical section so send reply
					self.send_reply(recvmsg)

			elif self._state == MonitorState.IN_CRITICAL_SECTION:
				if recvmsg.msg_type == MessageType.RA_REQUEST:
					if recvmsg.payload.get('monitor_id') != self.id:
						self.send_reply(recvmsg)
					else:
						self._pending_requests += [recvmsg]

	# Called before every method decorated with @monitor_entry.
	def lock(self):
		self.send_request()
		self._state = MonitorState.WAITING_FOR_REPLIES
		self._lock.acquire()
		logger('enters critical section, state %d' % self._state_stamp, self.fields(), color='yellow')

	# Called after every method decorated with @monitor_entry.
	def release(self):
		self.handle_pending_requests()
		self._state = MonitorState.IDLE
		logger('leaves critical section, state %d' % self._state_stamp, self.fields(), color='green')

def monitor_entry(func):
	def func_wrapper(self, *args, **kwargs):
		self.lock()
		retval = func(self, *args, **kwargs)
		self.release()
		return retval
	return func_wrapper

# A wrapper for messages passed between processes.
class Message:
	def __init__(self, msg_type, **kwargs):
		self.sender = MPI.COMM_WORLD.Get_rank()
		self.msg_type = msg_type
		self.payload = kwargs

	def send_to(self, destination):
		return MPI.COMM_WORLD.isend(self,
			dest = destination,
			tag = self.msg_type)

	def broadcast(self):
		# TODO: maybe switch to MPI broadcast
		for i in range(0, MPI.COMM_WORLD.size):
			if i != MPI.COMM_WORLD.Get_rank():
				self.send_to(i)

	@staticmethod
	def wait_for(**kwargs):
		req = MPI.COMM_WORLD.irecv(**kwargs)
		return req.wait()

# Enumerates types of messages passed between processes.
class MessageType:
	RA_REQUEST = 1				# request to get to critical section
	RA_REPLY = 2				# reply to a process's request
	SIGNAL = 3					# notification of freeing a conditional variable

# Enumerates the state a monitor is in.
class MonitorState:
	IDLE = 0					# doing nothing
	WAITING_FOR_SIGNAL = 1		# waiting on variable: _waiting_on
	WAITING_FOR_REPLIES = 2		# waiting for RA_REPLY to get to crit. section
	IN_CRITICAL_SECTION = 3		# performing operations in critical section