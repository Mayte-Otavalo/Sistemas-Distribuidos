from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

serverName = input("Enter server hostname or IP address: ")
if not serverName:
    serverName = "localhost"
try:
    serverPort = int(input("Enter server port number: "))
except:
    print("Invalid input. Using default port 12000.")
    serverPort = 12000

if serverPort <= 0 or serverPort > 65535:
    serverPort = 12000

# Create server
with SimpleXMLRPCServer((serverName, serverPort),
                         requestHandler=RequestHandler) as server:
    server.register_introspection_functions()

    # Register a function under a different name
    def add(x, y):
        return x + y

    server.register_function(add, 'add')

    # Run the server's main loop
    print(f"Server is listening on {serverName}:{serverPort}...")
    server.serve_forever()

