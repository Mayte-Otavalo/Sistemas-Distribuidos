import xmlrpc.client
import numpy as np


serverName = input(
    "Enter server IP [localhost]: "
).strip()

if not serverName:
    serverName = "localhost"


try:
    serverPort = int(
        input("Enter server port [12000]: ").strip()
        or "12000"
    )
except ValueError:
    serverPort = 12000


proxy = xmlrpc.client.ServerProxy(
    f"http://{serverName}:{serverPort}/RPC2",
    allow_none=True
)


try:
    n = int(
        input("Square matrix size n [2]: ").strip()
        or "2"
    )
except ValueError:
    n = 2


operation = input(
    "Operation (add/sub/prod) [add]: "
).strip().lower()

if not operation:
    operation = "add"


A = np.random.randint(
    1,
    10,
    size=(n, n)
)

B = np.random.randint(
    1,
    10,
    size=(n, n)
)


print("\nMatrix A:")
print(A)

print("\nMatrix B:")
print(B)

print("\nOperation:")
print(operation)


result = proxy.matrix_operation(
    A.tolist(),
    B.tolist(),
    operation
)


print("\nResult returned by server:")
print(np.array(result))