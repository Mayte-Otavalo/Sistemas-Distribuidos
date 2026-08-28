import zmq


context = zmq.Context()

subscriber = context.socket(zmq.SUB)


publisher_count = int(
    input(
        "How many publishers "
        "do you want to connect to? "
    )
)


for i in range(publisher_count):

    host = input(
        f"Publisher {i + 1} IP [localhost]: "
    ).strip()

    if not host:
        host = "localhost"

    port = int(
        input(
            f"Publisher {i + 1} port: "
        )
    )

    endpoint = (
        f"tcp://{host}:{port}"
    )

    subscriber.connect(endpoint)

    print(
        "Connected to",
        endpoint
    )


topics = input(
    "Topics separated by spaces "
    "(example: TIME RANDOM): "
).upper().split()


for topic in topics:

    subscriber.setsockopt_string(
        zmq.SUBSCRIBE,
        topic
    )


print(
    "Waiting for messages. "
    "Ctrl+C to stop."
)


while True:

    message = subscriber.recv_string()

    print(
        "Received:",
        message
    )