from mpi4py import MPI
from dmon_utils import *
import thread, random, time
from monitors import *

comm = MPI.COMM_WORLD
comm.Barrier()
rank = MPI.COMM_WORLD.Get_rank()
size = MPI.COMM_WORLD.size

if __name__ == '__main__':

	rwm = ReadersWritersMonitor(123)

	if rank < 2: # consumer
		logger('Consumer #', rank, 'and I can see', size, 'processes.')
		while True:
			time.sleep(random.random() * 3)
			logger('attempting to get')
			x = rwm.get()
			logger('got', x)

	else: # producer
		logger('Producer #', rank, 'and I can see', size, 'processes.')
		i = 0
		while True:
			time.sleep(random.random() * 3)
			logger('attempting to insert')
			rwm.insert()
			logger('inserted')
			i += 1