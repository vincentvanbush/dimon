from mpi4py import MPI
from dmon_utils import *
import thread

comm = MPI.COMM_WORLD
comm.Barrier()

if __name__ == '__main__':
	

	print 'I am', rank, 'and I can see', size, 'processes.'

	if rank == 0:
		msg = Message(MessageType.RA_REQUEST, spurdo = 'sparde')
		msg.multicast(1)
	elif rank == 1:
		msg = Message.wait_for(source = 0, tag = MessageType.MSG_RA_REQUEST)
		print 'Sender: ', msg.sender
		print 'Msg type: ', msg.msg_type
		print 'Content: ', msg.payload
	else:
		print 'I have nothing to do'