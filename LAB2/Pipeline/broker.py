import zmq
import pickle


context = zmq.Context()


input_socket = context.socket(
    zmq.PULL
)

output_socket = context.socket(
    zmq.PUSH
)


input_socket.bind(
    "tcp://*:13000"
)

output_socket.bind(
    "tcp://*:13001"
)


print(
    "Broker ready: "
    "input 13000 -> output 13001"
)


while True:

    message = input_socket.recv()

    work = pickle.loads(message)

    print(
        "Broker received:",
        work
    )

    output_socket.send(message)

    print(
        "Broker forwarded:",
        work
    )