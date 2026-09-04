import socket

ENTITY_ID = "mayte"
PORT = 50001

sock = socket.socket(
    socket.AF_INET,
    socket.SOCK_DGRAM
)

sock.setsockopt(
    socket.SOL_SOCKET,
    socket.SO_REUSEADDR,
    1
)

sock.bind(("", PORT))

print("Entity waiting for location requests...")

while True:

    data, addr = sock.recvfrom(1024)

    message = data.decode()

    if message == ENTITY_ID:

        response = (
            f"{ENTITY_ID}:"
            f"{socket.gethostbyname(socket.gethostname())}"
        )

        sock.sendto(
            response.encode(),
            addr
        )