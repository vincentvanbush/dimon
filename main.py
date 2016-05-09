from monitors import *
from dmon_utils import logger
from mpi4py import MPI
import sys

if __name__ == '__main__':
	comm = MPI.COMM_SELF.Spawn(sys.executable,
	                           args=['worker.py'],
	                           maxprocs=4)

	logger('Processes have been spawned')
	raw_input()