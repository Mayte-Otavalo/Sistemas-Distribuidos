import xmlrpc.client

# Create a client proxy
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

proxy = xmlrpc.client.ServerProxy(f"http://{serverName}:{serverPort}/RPC2")

# Call the remote method 'add'
result = proxy.add(8, 3)
print("8 + 3 =", result)
