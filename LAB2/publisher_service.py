import zmq
import time
import random
import sys


if len(sys.argv) < 3:
    print(
        "Usage: python3 publisher_service.py "
        "SERVICE PORT"
    )

    print(
        "Example: "
        "python3 publisher_service.py TIME 15001"
    )

    sys.exit(1)


service = sys.argv[1].upper()
port = int(sys.argv[2])


context = zmq.Context()

publisher = context.socket(zmq.PUB)

publisher.bind(
    f"tcp://*:{port}"
)


print(
    f"Publisher {service} "
    f"listening on port {port}..."
)


time.sleep(1)

count = 0


while True:

    count += 1

    if service == "TIME":

        data = time.asctime()

    elif service == "RANDOM":

        data = str(
            random.randint(1, 100)
        )

    else:

        data = f"Message #{count}"


    message = f"{service} {data}"

    publisher.send_string(message)

    print("Sent:", message)

    time.sleep(2)