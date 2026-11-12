# SISTEMA DISTRIBUIDO CON SEGURIDAD (CALIDAD DEL AIRE)

Este directorio contiene **únicamente los archivos esenciales** para la operación en producción del sistema distribuido de aprendizaje federado con su sistema de seguridad integral (cifrado Fernet, delimitación de tramas TCP y validación de esquemas).

---

## 1. Estructura de Archivos Esenciales

```text
SISTEMA_DISTRIBUIDO_SEGURIDAD/
├── client/                               # Módulo del Cliente Federado (Nodos 1 y 2)
│   ├── .client_1.key                     # Clave simétrica Fernet privada de Cliente 1 (PC 2)
│   ├── .client_2.key                     # Clave simétrica Fernet privada de Cliente 2 (Raspberry Pi)
│   ├── client.py                         # Proceso principal de ejecución de clientes federados
│   ├── communication.py                  # Comunicación TCP cliente, framing y cifrado
│   ├── data_loader.py                    # Carga y aislamiento de particiones de datos locales
│   ├── encryption.py                     # Gestor de seguridad y cifrado Fernet del cliente
│   ├── local_training.py                 # Ciclo de entrenamiento local (PyTorch) y cálculo de deltas
│   └── local_data/                       # Particiones locales de datos privados
│       ├── client_1/                     # Datos privados de Cliente 1 (iid, non-iid, val)
│       └── client_2/                     # Datos privados de Cliente 2 (iid, non-iid, val)
├── server/                               # Módulo del Servidor Coordinador (Nodo 0)
│   ├── aggregation.py                    # Algoritmo de agregación federada FedAvg
│   ├── communication.py                  # Servidor TCP concurrente, recepción de tramas y descifrado
│   ├── encryption.py                     # Gestor de claves y cifrado Fernet para cada cliente
│   ├── evaluation.py                     # Evaluación del modelo global sobre conjuntos no vistos
│   ├── fault_tolerance.py                # Tolerancia a fallos, persistencia, idempotencia y logs
│   ├── global_model.py                   # Definición de la red neuronal MLP (PyTorch)
│   ├── global_test.csv                   # Conjunto de prueba global no visto para evaluación
│   ├── global_val.csv                    # Conjunto de validación global
│   ├── server.py                         # Proceso principal del Servidor Coordinador
│   ├── checkpoints/                      # Almacén de checkpoints atómicos de rondas
│   └── logs/                             # Registro estructurado de eventos y fallos
├── schemas/                              # Validación formal de mensajería
│   ├── message.xsd                       # Esquema XSD para validar mensajes XML
│   ├── request.schema.json               # Esquema JSON Schema para peticiones cliente
│   └── response.schema.json              # Esquema JSON Schema para respuestas del servidor
├── protocol.py                           # Delimitación de tramas TCP (4 bytes header), serialización y esquemas
├── requirements.txt                      # Dependencias exactas requeridas de Python
├── test_comm_and_security.py             # Script de verificación de red, esquemas y cifrado
├── run_demo_local.py                     # Demostración local integral (servidor + 2 clientes en 1 solo comando)
└── README.md                             # Esta guía de uso y despliegue
```

---

## 2. Componentes de Seguridad Implementados

1. **Cifrado Simétrico Autenticado (Fernet / AES-128-CBC + HMAC-SHA256)**:
   - Cada cliente dispone de una clave secreta independiente (`.client_1.key`, `.client_2.key`).
   - El servidor mantiene el almacén de claves en `server/encryption.py` asociadas por ID de cliente.
   - Todo el tráfico de pesos, deltas y reportes viaja encriptado y autenticado.
2. **Delimitación de Tramas (Message Framing en `protocol.py`)**:
   - Encabezado binario de 4 bytes (`>I`) que previene la fragmentación o solapamiento en el buffer TCP.
3. **Validación Estricta de Integridad y Esquemas**:
   - Validación con **JSON Schema** (`request.schema.json`, `response.schema.json`).
   - Validación con **XML XSD** (`message.xsd`).
   - Validación semántica programática en `protocol.py`.
4. **Idempotencia y Tolerancia a Fallos (`server/fault_tolerance.py`)**:
   - Cada mensaje incluye un identificador único (UUID). Mensajes retransmitidos o duplicados son descartados automáticamente.
   - Checkpoints atómicos para recuperarse ante caídas imprevistas.

---

## 3. Requisitos e Instalación

Instalar las dependencias en cada nodo (o entorno virtual):

```bash
pip install -r requirements.txt
```

---

## 4. Instrucciones de Ejecución con Seguridad Activada

### 4.1. Verificación Inicial de Seguridad y Comunicación
Antes de iniciar los nodos, puede validar que el sistema de cifrado y sockets funciona correctamente ejecutando:

```bash
python test_comm_and_security.py
```

### 4.2. Demostración Todo en Uno en Local (Servidor + 2 Clientes con 1 solo comando)
Para probar todo el flujo federado de extremo a extremo sin tener que abrir 3 terminales:

```bash
# Ejecutar 2 rondas con cifrado Fernet activo
python run_demo_local.py --rounds 2

# Ejecutar 5 rondas completas
python run_demo_local.py --rounds 5
```

### 4.3. Despliegue Manual o en 3 Máquinas Físicas (LAN)
En la máquina que actúa como servidor (escuchando en el puerto TCP 5000 con cifrado activado):

```bash
python server/server.py --host 0.0.0.0 --port 5000 --rounds 5 --min-clients 2 --encryption
```

*Si desea que utilice serialización XML en lugar de JSON:*
```bash
python server/server.py --host 0.0.0.0 --port 5000 --rounds 5 --min-clients 2 --encryption --format xml
```

*Si el servidor se cayó y desea restaurar desde el último checkpoint:*
```bash
python server/server.py --host 0.0.0.0 --port 5000 --rounds 5 --min-clients 2 --encryption --restore
```

### 4.3. Iniciar Nodo 1: Cliente 1 (PC 2)
En el segundo equipo (o en otra terminal en pruebas locales cambiando la IP a `127.0.0.1`):

```bash
python client/client.py --client-id client_1 --server-host <IP_DEL_SERVIDOR> --server-port 5000 --distribution iid --rounds 5 --encryption
```

### 4.4. Iniciar Nodo 2: Cliente 2 (Raspberry Pi)
En el nodo Raspberry Pi (o tercera terminal en local):

```bash
python client/client.py --client-id client_2 --server-host <IP_DEL_SERVIDOR> --server-port 5000 --distribution iid --rounds 5 --encryption
```
