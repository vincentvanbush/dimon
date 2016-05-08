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

	if rank < 2:
		print 'Consumer #', rank, 'and I can see', size, 'processes.'
		i = 0
		while True:
			time.sleep(random.random() * 3)
			x = rwm.get()
			print 'Consumer #', rank, 'got', x

	else:
		print 'Producer #', rank, 'and I can see', size, 'processes.'
		i = 0
		while True:
			time.sleep(random.random() * 3)
			rwm.insert(i)
			print 'Producer #', rank, 'inserted', i