from dmon_utils import *

CONDITION_VAR_EMPTY = 0
CONDITION_VAR_FULL = 1

class ReadersWritersMonitor:
	def __init__(self, id):
		self.id = id
		self.pool = []
		self.inp = 0
		self.out = 0
		self.count = 0
		self.empty = ConditionVar(CONDITION_VAR_EMPTY)
		self.full = ConditionVar(CONDITION_VAR_FULL)

	@monitor_entry
	def insert(self, what):
		# magic
		pass

	@monitor_entry
	def get(self, what):
		# magic
		pass