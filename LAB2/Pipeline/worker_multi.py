import zmq
import time
import pickle
import sys


if len(sys.argv) > 1:
    worker_id = sys.argv[1]
else:
    worker_id = "W1"


if len(sys.argv) > 2:
    broker_ip = sys.argv[2]
else:
    broker_ip = "localhost"


context = zmq.Context()

receiver = context.socket(
    zmq.PULL
)


receiver.connect(
    f"tcp://{broker_ip}:13001"
)


print(
    f"Worker {worker_id} "
    f"connected to broker "
    f"{broker_ip}:13001"
)


while True:

    work = pickle.loads(
        receiver.recv()
    )

    print(
        f"Worker {worker_id} received:",
        work
    )

    time.sleep(
        work["workload"] * 0.1
    )

    print(
        f"Worker {worker_id} "
        f"completed task "
        f"{work['task']} "
        f"from {work['source']}"
    )