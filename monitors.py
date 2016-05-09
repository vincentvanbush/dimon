from dmon_utils import *
import random, time

CONDITION_VAR_EMPTY = 0
CONDITION_VAR_FULL = 1
MAX = 5

class ReadersWritersMonitor(Monitor):
	def __init__(self, id):
		Monitor.__init__(self, id)

		# Local variables
		self.__pool = [None, None, None, None, None]
		self.__inp = 0
		self.__out = 0
		self.__count = 0

		# Condition variables identified by monitor ID and var ID
		self.__empty = ConditionVar(CONDITION_VAR_EMPTY, self)
		self.__full = ConditionVar(CONDITION_VAR_FULL, self)

	# All subclasses of Monitor need to specify the list of
	# variables that are passed to other processes as
	# the distributed object's state.

	def shared_vars(self):
		return ['__pool', '__inp', '__out', '__count']

	# Monitor entries decorated with @monitor_entry are executed
	# in mutual exclusion.

	@monitor_entry
	def insert(self):
		while self.__count == MAX:
			self.__full.wait()
		if len([x for x in self.__pool if x != None]) > 0:
			newelem = max([x for x in self.__pool if x != None]) + 1
		else:
			newelem = 1
		self.__pool[self.__inp] = newelem
		self.__inp = (self.__inp + 1) % MAX
		self.__count += 1
		time.sleep(random.random() * 2)
		self.__empty.signal()
		
	@monitor_entry
	def get(self):
		while self.__count == 0:
			self.__empty.wait()
		what = self.__pool[self.__out]
		self.__pool[self.__out] = None
		self.__out = (self.__out + 1) % MAX
		self.__count -= 1
		self.__full.signal()
		return what
		