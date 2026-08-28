import zmq, time, pickle, sys

context = zmq.Context()
r = context.socket(zmq.PULL)
me = str(sys.argv[1])


serverName = "localhost"
serverPort = 13000

if serverPort <= 0 or serverPort > 65535:
    serverPort = 13000

p = "tcp://" + serverName + ":" + str(serverPort)

r.connect(p)

count = 0
while True:
    work = pickle.loads(r.recv())

    count += 1

    print(
        "Worker", me,
        "Work received:", work
    )

    time.sleep(work[0] * 0.1)
