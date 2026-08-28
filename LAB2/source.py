import zmq
import time
import pickle
import random

context = zmq.Context()

s = context.socket(zmq.PUSH)

serverPort = 13000

p = "tcp://*:" + str(serverPort)

s.bind(p)

for i in range(10):
    workload = random.randint(1, 100)

    work = (workload, i)

    print("Sending:", work)

    s.send(pickle.dumps(work))

    time.sleep(0.1)
