import zmq, time

context = zmq.Context()
s = context.socket(zmq.PUB)

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
s.bind(p)

cont = 0
while True:
    time.sleep(5)
    cont += 1
    s.send(("TIME " + time.asctime() + " - Message #" + str(cont)).encode("utf-8"))

