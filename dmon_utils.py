from mpi4py import MPI
import time

class ConditionVar:
	def __init__(self, var_id, monitor):
		self.var_id = var_id
		self.monitor = monitor

	def wait(self):
		self.monitor.handle_pending_requests()
		self.monitor._waiting_on = self
		self.monitor._state = MonitorState.WAITING_FOR_SIGNAL
		self.monitor._lock.acquire() # suspend until signal is received
		pass

	def signal(self):
		signal = Message(MessageType.SIGNAL(
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
		thread.start_new_thread(_listener_routine, (self))

	def _listener_routine(self):

		# Release the critical section
		def handle_pending_requests():
			self._state_stamp += 1
			m = Message(MessageType.RA_REPLY,
				monitor_id = self.id,
				state_stamp = self._state_stamp)
			for r in self._pending_requests:
				m.send(r.sender)
			self._pending_requests = []

		def reply(recvmsg):
			field_state = self.fields()
			reply = Message(
				MessageType.RA_REPLY,
				monitor_id = self.id,
				field_state = fields())
			reply.send_to(recvmsg.sender)

		self._lock.acquire()
		while true:
			recvmsg = Message.wait_for()

			# Process the message dependent on the state receiver is in.
			if _state == MonitorState.IDLE:
				if recvmsg.msg_type == MessageType.RA_REQUEST:
					reply(recvmsg)
				
			elif _state == MonitorState.WAITING_FOR_REPLIES:

				if recvmsg.msg_type == MessageType.RA_REQUEST:
					if _last_request == None or \
					   recvmsg.timestamp < _last_request.payload.get('timestamp') or \
					   recvmsg.payload.get('monitor_id') != self.id:
						reply(recvmsg)
					else:
						_pending_requests += [recvmsg]

				elif recvmsg.msg_type == MessageType.RA_REPLY:
					if recvmsg.payload.get('monitor_id') == self.id:
						recvstamp = recvmsg.payload.get('state_stamp')
						if recvstamp > self._state_stamp
							self._state_stamp = recvstamp
							fields = recvmsg.payload.get('field_state')
							for k in fields:
								self.__dict__[k] = fields[k]
						self._replies_count += 1
						if self.replies_count >= MPI.COMM_WORLD.size - 1:
							self._state = MonitorState.IN_CRITICAL_SECTION
							self.replies_count = 0

			elif _state == MonitorState.WAITING_FOR_SIGNAL:
				if recvmsg.msg_type == MessageType.SIGNAL and \
				   recvmsg.payload.get('var_id') == self._waiting_on and \
				   recvmsg.payload.get('monitor_id') == self.id:
					request = Message(
						MessageType.RA_REQUEST,
						timestamp = time.time(),
						monitor_id = self.id,
						var_id = _waiting_on.id)
					request.broadcast()
					self._last_request = request
					self._replies_count = 
					self._state = MonitorState.WAITING_FOR_REPLIES

				elif recvmsg.msg_type == MessageType.RA_REQUEST:
					# not in critical section so send reply
					reply = Message(
						MessageType.RA_REPLY,
						monitor_id = self.id)
					reply.send_to(recvmsg.sender)

			elif _state == MonitorState.IN_CRITICAL_SECTION:
				
				if recvmsg.msg_type == MessageType.RA_REQUEST:
					if recvmsg.monitor_id != self.id:
						reply = Message(
							MessageType.RA_REPLY,
							monitor_id = self.id)
						reply.send_to(recvmsg.sender)
					else:
						self._pending_requests += [recvmsg]

	# Called before every method decorated with @monitor_entry.
	def lock(self):
		request = Message(
			MessageType.RA_REQUEST,
			timestamp = time.time(),
			monitor_id = self.id)
		self._state = MonitorState.WAITING_FOR_REPLIES
		self._replies_count = 0
		self._last_request = request
		request.broadcast()
		self._lock.acquire()
		print '(', time.time() ')', 'monitor', self.id, 'enters critical section'

	# Called after every method decorated with @monitor_entry.
	def release(self):
		self.handle_pending_requests()
		self._state = MonitorState.IDLE
		print '(', time.time() ')', 'monitor', self.id, 'leaves critical section'

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