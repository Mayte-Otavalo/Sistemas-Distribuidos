# Importación de módulos necesarios de la biblioteca estándar
import socket  # Permite interactuar con la red y resolver nombres/direcciones IP
import uuid  # Proporciona funciones para generar identificadores únicos universales (UUID)

# Generación de un UUID versión 5 (basado en hash SHA-1)
# Utiliza un espacio de nombres estándar (NAMESPACE_DNS) y una cadena ("student-a")
# Al ser determinista, la combinación de este espacio de nombres y el texto siempre producirá el mismo UUID
entity_id = uuid.uuid5(uuid.NAMESPACE_DNS, "student-a")

# Obtención de la información de red del host local
hostname = socket.gethostname()  # Obtiene el nombre del equipo en la red local
ip = socket.gethostbyname(
    hostname
)  # Resuelve el nombre del host a su dirección IPv4 correspondiente

# Impresión de los metadatos iniciales generados
print("Entity ID :", entity_id)
print("Hostname  :", hostname)
print("Address   :", ip)

# Creación de una estructura de datos (diccionario) que representa a la entidad
# 'id' se convierte a cadena de texto para facilitar serialización o compatibilidad
# 'address' almacena una tupla con la IP y el puerto de red (formato estándar de sockets)
entity = {"id": str(entity_id), "address": (ip, 5000)}

# Muestra el estado inicial del diccionario
print(entity)

# Modificación del puerto en la dirección de la entidad (cambia del puerto 5000 al 6000)
entity["address"] = (ip, 6000)

# Muestra el estado del diccionario tras la actualización
print(entity)