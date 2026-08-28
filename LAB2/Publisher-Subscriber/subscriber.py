import zmq

context = zmq.Context()
s = context.socket(zmq.SUB)

serverName = input("Enter server hostname or IP address: ")
if not serverName:
    serverName = "localhost"
try:
    serverPort = int(input("Enter server port number: "))
except:
    print("Invalid input. Using default port 15000.")
    serverPort = 15000

if serverPort <= 0 or serverPort > 65535:
    serverPort = 15000

p = "tcp://" + serverName + ":" + str(serverPort)
s.connect(p)

s.setsockopt_string(zmq.SUBSCRIBE, "TIME")

for i in range(5):
    time = s.recv().decode("utf-8")
    print(time)

