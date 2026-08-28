import zmq
import time
import pickle
import random
import sys


if len(sys.argv) > 1:
    source_id = sys.argv[1]
else:
    source_id = "S1"


if len(sys.argv) > 2:
    broker_ip = sys.argv[2]
else:
    broker_ip = "localhost"


context = zmq.Context()

sender = context.socket(
    zmq.PUSH
)


sender.connect(
    f"tcp://{broker_ip}:13000"
)


print(
    f"Source {source_id} "
    f"connected to broker "
    f"{broker_ip}:13000"
)


for i in range(5):

    work = {
        "source": source_id,
        "task": i,
        "workload": random.randint(1, 5)
    }

    print(
        "Sending:",
        work
    )

    sender.send(
        pickle.dumps(work)
    )

    time.sleep(0.2)