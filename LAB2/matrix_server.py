from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import numpy as np


class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)


serverName = input("Enter server hostname/IP [0.0.0.0]: ").strip()

if not serverName:
    serverName = "0.0.0.0"


try:
    serverPort = int(
        input("Enter server port [12000]: ").strip() or "12000"
    )
except ValueError:
    serverPort = 12000


if serverPort <= 0 or serverPort > 65535:
    serverPort = 12000


def matrix_operation(matrix_a, matrix_b, operation):

    A = np.array(matrix_a)
    B = np.array(matrix_b)

    if operation == "add":
        result = A + B

    elif operation == "sub":
        result = A - B

    elif operation == "prod":
        result = np.matmul(A, B)

    else:
        raise ValueError(
            "Invalid operation. Use add, sub or prod."
        )

    print("\nOperation received:", operation)

    print("\nMatrix A:")
    print(A)

    print("\nMatrix B:")
    print(B)

    print("\nResult:")
    print(result)

    return result.tolist()


with SimpleXMLRPCServer(
    (serverName, serverPort),
    requestHandler=RequestHandler,
    allow_none=True
) as server:

    server.register_introspection_functions()

    server.register_function(
        matrix_operation,
        "matrix_operation"
    )

    print(
        f"Matrix server listening on "
        f"{serverName}:{serverPort}..."
    )

    server.serve_forever()