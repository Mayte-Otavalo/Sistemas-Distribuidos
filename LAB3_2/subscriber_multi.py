import zmq
import ldap
import ldap.filter
import getpass
import sys


# ---------------------------------------
# CONFIGURACIÓN LDAP
# ---------------------------------------

LDAP_SERVER = "ldap://localhost"

LDAP_USER = (
    "uid=francisco,"
    "ou=People,"
    "dc=rolando,"
    "dc=com"
)

LDAP_SERVICES_BASE = (
    "ou=Services,"
    "dc=rolando,"
    "dc=com"
)


# ---------------------------------------
# PEDIR SERVICIOS
# ---------------------------------------

topics = input(
    "Services separated by spaces "
    "(example: TIME RANDOM): "
).upper().split()


if not topics:

    print("No services entered.")
    sys.exit(1)


# ---------------------------------------
# AUTENTICACIÓN LDAP
# ---------------------------------------

ldap_password = getpass.getpass(
    "LDAP password for francisco: "      #aqui se pide la contraseña del usuario y es (password)
)

conn = ldap.initialize(
    LDAP_SERVER
)


try:

    conn.simple_bind_s(
        LDAP_USER,
        ldap_password
    )

    print(
        "LDAP authentication successful!"
    )


except ldap.INVALID_CREDENTIALS:

    print(
        "LDAP authentication failed!"
    )

    sys.exit(1)


except ldap.LDAPError as e:

    print(
        "LDAP error:",
        e
    )

    sys.exit(1)


# ---------------------------------------
# CREAR SUBSCRIBER ZEROMQ
# ---------------------------------------

context = zmq.Context()

subscriber = context.socket(              #zmq.SUB es para suscribirse a un servicio
    zmq.SUB
)

connected_services = 0


# ---------------------------------------
# BUSCAR CADA SERVICIO EN LDAP
# ---------------------------------------

for topic in topics:                     #aqui se busca cada servicio en LDAP en cada ciclo

    search_filter = (
        ldap.filter.filter_format(          #aqui se crea el filtro de búsqueda
            "(cn=%s)",                      #cn es el atributo que se busca
            [topic]
        )
    )

    results = conn.search_s(
        LDAP_SERVICES_BASE,
        ldap.SCOPE_ONELEVEL,
        search_filter,
        [
            "ipHostNumber",
            "ipServicePort"
        ]
    )


    if not results:

        print(
            f"Service {topic} "
            "not found in LDAP."
        )

        continue


    dn, attributes = results[0]


    try:

        host = (
            attributes[
                "ipHostNumber"
            ][0].decode("utf-8")
        )

        port = int(
            attributes[
                "ipServicePort"
            ][0].decode("utf-8")
        )


    except KeyError:

        print(
            f"Service {topic} does not "
            "contain IP or port."
        )

        continue


    endpoint = (
        f"tcp://{host}:{port}"
    )


    subscriber.connect(
        endpoint
    )


    subscriber.setsockopt_string(           #aqui se establece el filtro de búsqueda
        zmq.SUBSCRIBE,
        topic
    )


    print(
        f"Service {topic} found in LDAP"
    )

    print(
        "IP:",
        host
    )

    print(
        "Port:",
        port
    )

    print(
        "Connected to:",
        endpoint
    )

    connected_services += 1


# LDAP ya no es necesario una vez
# obtenidas las direcciones.

conn.unbind_s()


# ---------------------------------------
# RECIBIR MENSAJES
# ---------------------------------------

if connected_services == 0:               #aqui se comprueba si se conectaron a alguno de los servicios

    print(
        "No services available."
    )

    subscriber.close()
    context.term()

    sys.exit(1)


print(
    "\nWaiting for messages. "
    "Ctrl+C to stop."
)


try:

    while True:

        message = (
            subscriber.recv_string()
        )

        print(
            "Received:",
            message
        )


except KeyboardInterrupt:

    print(
        "\nSubscriber stopped."
    )


finally:

    subscriber.close()

    context.term()