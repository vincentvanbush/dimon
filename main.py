from monitors import *
from mpi4py import MPI
import sys

if __name__ == '__main__':
	comm = MPI.COMM_SELF.Spawn(sys.executable,
	                           args=['worker.py'],
	                           maxprocs=5)

	print 'Processes have been spawned'

	# rwm = ReadersWritersMonitor(123)
	# rwm.insert(123)