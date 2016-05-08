from dmon_utils import *

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
		self.__empty = ConditionVar(id, CONDITION_VAR_EMPTY)
		self.__full = ConditionVar(id, CONDITION_VAR_FULL)

	# All subclasses of Monitor need to specify the list of
	# variables that are passed to other processes as
	# the distributed object's state.
	def fields():
		return {
			'__pool': __pool,
			'__inp': __inp,
			'__out': __out,
			'__count': __count
		}

	# Monitor entries decorated with @monitor_entry are executed
	# in mutual exclusion.

	@monitor_entry
	def insert(self, what):
		while self.__count == MAX:
			self.__full.wait()
		self.__pool[inp] = what
		self.__inp = (self.__inp + 1) % MAX
		self.__count += 1
		
	@monitor_entry
	def get(self, what):
		while self.__count == 0:
			self.__empty.wait()
		elem = self.__pool[self.__out]
		self.__out = (self.__out + 1) % MAX
		self.__count -= 1