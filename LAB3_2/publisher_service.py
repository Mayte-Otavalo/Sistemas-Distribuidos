import zmq
import time
import random
import sys
import ldap
import getpass


# ---------------------------------------
# CONFIGURACIÓN LDAP
# ---------------------------------------

LDAP_SERVER = "ldap://localhost"

LDAP_ADMIN = (
    "cn=admin,"
    "dc=rolando,"
    "dc=com"
)

LDAP_SERVICES_BASE = (
    "ou=Services,"
    "dc=rolando,"
    "dc=com"
)


# ---------------------------------------
# ARGUMENTOS
# ---------------------------------------

if len(sys.argv) < 3:

    print(
        "Usage: python3 publisher_service.py "
        "SERVICE PORT [IP]"
    )

    print(
        "Example: "
        "python3 publisher_service.py TIME 15001"
    )

    sys.exit(1)


service = sys.argv[1].upper() 

try:
    port = int(sys.argv[2]) #esta linea es para que el programa pueda recibir el puerto como un argumento

except ValueError:
    print("Invalid port")
    sys.exit(1)


if port <= 0 or port > 65535: #esto es para que el programa pueda recibir el puerto como un argumento
    print("Invalid port")
    sys.exit(1)


# Si Publisher y Subscriber están en la misma máquina
# usamos 127.0.0.1 por defecto.
#
# También puedes pasar una IP como tercer argumento.
if len(sys.argv) >= 4:
    publisher_ip = sys.argv[3]
else:
    publisher_ip = "127.0.0.1"


# ---------------------------------------
# ZEROMQ
# ---------------------------------------

context = zmq.Context()

publisher = context.socket(zmq.PUB) #zmq.PUB es para publicar mensajes

publisher.bind(
    f"tcp://*:{port}"
)


print(
    f"Publisher {service} "
    f"listening on port {port}..."
)


# ---------------------------------------
# REGISTRAR SERVICIO EN LDAP
# ---------------------------------------

ldap_password = getpass.getpass(
    "LDAP admin password: "
)

conn = ldap.initialize(
    LDAP_SERVER
)

try:                                #esto es para que el programa pueda recibir el puerto como un argumento

    conn.simple_bind_s(             #coloca el DN y la contraseña del administrador de LDAP
        LDAP_ADMIN,
        ldap_password
    )

    service_dn = (                   #aqui se crea el DN del servicio
        f"cn={service},"
        f"{LDAP_SERVICES_BASE}"       #aqui se coloca el DN base de servicios
    )

    attributes = [                   #attributes es un diccionario que contiene los atributos que se van a añadir al servicio
        (
            "objectClass",
            [
                b"top",
                b"ipService",
                b"extensibleObject"
            ]
        ),
        (
            "cn",
            [
                service.encode("utf-8")
            ]
        ),
        (
            "ipServicePort",
            [
                str(port).encode("utf-8")
            ]
        ),
        (
            "ipServiceProtocol",
            [
                b"tcp"
            ]
        ),
        (
            "ipHostNumber",
            [
                publisher_ip.encode("utf-8")
            ]
        )
    ]

    try:                            #try hace que el programa pueda recibir el puerto como un argumento

        conn.add_s(
            service_dn,
            attributes
        )

        print(
            "Service registered in LDAP:"
        )

    except ldap.ALREADY_EXISTS:      #si el servicio ya existe, se actualizan los atributos

        # Si el servicio ya existe,
        # actualizamos IP y puerto.

        conn.modify_s(
            service_dn,
            [
                (
                    ldap.MOD_REPLACE,       #se modifican los atributos
                    "ipHostNumber",
                    [
                        publisher_ip.encode(
                            "utf-8"
                        )
                    ]
                ),
                (
                    ldap.MOD_REPLACE,
                    "ipServicePort",
                    [
                        str(port).encode(
                            "utf-8"
                        )
                    ]
                )
            ]
        )

        print(
            "Service already existed."
        )

        print(
            "LDAP information updated."
        )


    print("Service:", service)
    print("IP:", publisher_ip)
    print("Port:", port)


except ldap.INVALID_CREDENTIALS:            #si el DN o la contraseña son incorrectos

    print(
        "Invalid LDAP administrator credentials"
    )

    sys.exit(1)


except ldap.LDAPError as e:

    print(
        "LDAP error:",
        e
    )

    sys.exit(1)


finally:

    conn.unbind_s()


# ---------------------------------------
# PUBLICAR MENSAJES
# ---------------------------------------

time.sleep(1)                            #se espera 1 segundo para que el servicio se registre en LDAP

count = 0


try:

    while True:

        count += 1

        if service == "TIME":

            data = time.asctime()

        elif service == "RANDOM":

            data = str(
                random.randint(1, 100)
            )

        else:

            data = (
                f"Message #{count}"
            )


        message = (
            f"{service} {data}"
        )

        publisher.send_string(
            message
        )

        print(
            "Sent:",
            message
        )

        time.sleep(2)


except KeyboardInterrupt:

    print(
        "\nPublisher stopped."
    )


finally:

    publisher.close()

    context.term()