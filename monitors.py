from dmon_utils import *

CONDITION_VAR_EMPTY = 0
CONDITION_VAR_FULL = 1

class ReadersWritersMonitor(Monitor):
	def __init__(self, id):
		self.id = id
		self.__pool = []
		self.__inp = 0
		self.__out = 0
		self.__count = 0
		self.__empty = ConditionVar(CONDITION_VAR_EMPTY)
		self.__full = ConditionVar(CONDITION_VAR_FULL)

	@monitor_entry
	def insert(self, what):
		# magic
		pass

	@monitor_entry
	def get(self, what):
		# magic
		pass