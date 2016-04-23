class ConditionVar:
	def __init__(self, var_id):
		self.var_id = var_id

	def wait(self):
		# magic
		pass

	def signal(self):
		# magic
		pass

def monitor_entry(func):
	def func_wrapper(self, *args, **kwargs):
		# lock the monitor
		retval = func(self, *args, **kwargs)
		# unlock the monitor
		return retval
	return func_wrapper