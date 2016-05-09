# dimon
Fully transparent, Hoare-style monitors for shared objects in distributed computing, written in Python and utilizing MPI.

## Purpose

As the concept of a monitor has been ever-present in concurrent programming for many years, it looks like a good idea to transpose the idea into the realm of distributed computing.

The aim is to create a foundation class for an object shared between a number of MPI processes, allowing the programmer to subclass it and implement a Hoare-style monitor-based synchronization scheme (described [here](https://en.wikipedia.org/wiki/Monitor_(synchronization))).

The programmer can define a number of conditional variables on which typical `wait` and `signal` operations can be performed. Note that, to make things easier in an asynchronous distributed environmennt, the semantic of the `signal` operation is actually equivalent to `threading.Condition`'s `notify_all` method, waking all waiting processes instead of just one. This is in fact usually the recommended and safer option when using Hoare-style monitors anyway, so I doubt you'll miss a `notify` equivalent.

## Implementation

Mutual exclusion was implemented using an algorithm based on [Ricart-Agrawala's approach](https://en.wikipedia.org/wiki/Ricart%E2%80%93Agrawala_algorithm). Additionally, with each reply message processes pass their current local state of the object stamped with a sequential number to ensure that a process entering the critical section always sees the most recent state.

## Usage

If you are familiar with Hoare's monitor specification, head on over to [`monitors.py`](monitors.py) which contains an example class representing a shared object with two conditional variables and two entry methods. Run [`main.py`](main.py) to spawn a number of [`worker.py`](worker.py) processes using the monitor.

Requires Python 2.7 (tested with 2.7.6), an MPI environment and mpi4py.

### Disclaimer

This is an academic exercise. Feel free to use it whichever way you fancy, but be aware of it being an unfinished article :-)
