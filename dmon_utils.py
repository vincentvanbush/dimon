class ConditionVar:
	def __init__(self, var_id):
		self.var_id = var_id

	def wait(self):
		# magic
		pass

	def signal(self):
		# magic
		pass

class Monitor:
	def lock(self):
		print 'locking', self.id

	def release(self):
		print 'unlocking', self.id

def monitor_entry(func):
	def func_wrapper(self, *args, **kwargs):
		self.lock()
		retval = func(self, *args, **kwargs)
		self.release()
		return retval
	return func_wrapper