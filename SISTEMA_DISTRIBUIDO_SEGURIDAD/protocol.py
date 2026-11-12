"""
Protocolo de mensajería, serialización (JSON/XML), delimitación de tramas TCP
y validación de esquemas para AIR_QUALITY_DISTRIBUTED.
"""

import os
import json
import struct
import socket
import xml.etree.ElementTree as ET
from typing import Any, Dict, Tuple, Optional
import jsonschema
from lxml import etree

HEADER_FORMAT = '>I'
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

# Rutas a esquemas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")
REQUEST_SCHEMA_PATH = os.path.join(SCHEMAS_DIR, "request.schema.json")
RESPONSE_SCHEMA_PATH = os.path.join(SCHEMAS_DIR, "response.schema.json")
MESSAGE_XSD_PATH = os.path.join(SCHEMAS_DIR, "message.xsd")

# Cargar esquemas en memoria si existen
_REQUEST_JSON_SCHEMA = None
_RESPONSE_JSON_SCHEMA = None
_XML_SCHEMA_VALIDATOR = None

def load_schemas():
    global _REQUEST_JSON_SCHEMA, _RESPONSE_JSON_SCHEMA, _XML_SCHEMA_VALIDATOR
    if os.path.exists(REQUEST_SCHEMA_PATH):
        with open(REQUEST_SCHEMA_PATH, 'r', encoding='utf-8') as f:
            _REQUEST_JSON_SCHEMA = json.load(f)
    if os.path.exists(RESPONSE_SCHEMA_PATH):
        with open(RESPONSE_SCHEMA_PATH, 'r', encoding='utf-8') as f:
            _RESPONSE_JSON_SCHEMA = json.load(f)
    if os.path.exists(MESSAGE_XSD_PATH):
        xml_schema_doc = etree.parse(MESSAGE_XSD_PATH)
        _XML_SCHEMA_VALIDATOR = etree.XMLSchema(xml_schema_doc)

load_schemas()


# -------------------------------------------------------------
# 1. Delimitación de tramas TCP (Message Framing con Header)
# -------------------------------------------------------------
def send_frame(sock: socket.socket, data: bytes) -> None:
    """
    Envía un mensaje precedido por un encabezado de longitud de 4 bytes (Big-Endian).
    Garantiza que la trama no se mezcle ni fragmente lógicamente.
    """
    length = len(data)
    header = struct.pack(HEADER_FORMAT, length)
    sock.sendall(header + data)

def recv_exact(sock: socket.socket, num_bytes: int) -> Optional[bytes]:
    """Lee exactamente num_bytes del socket TCP o retorna None si se cierra."""
    buffer = bytearray()
    while len(buffer) < num_bytes:
        packet = sock.recv(num_bytes - len(buffer))
        if not packet:
            return None
        buffer.extend(packet)
    return bytes(buffer)

def recv_frame(sock: socket.socket) -> Optional[bytes]:
    """
    Lee una trama completa: primero los 4 bytes de encabezado y luego los bytes del payload.
    """
    header = recv_exact(sock, HEADER_SIZE)
    if not header:
        return None
    (length,) = struct.unpack(HEADER_FORMAT, header)
    return recv_exact(sock, length)


# -------------------------------------------------------------
# 2. Serialización y Deserialización (JSON y XML)
# -------------------------------------------------------------
def serialize_dict_to_xml(data: Dict[str, Any], root_tag: str = "request") -> bytes:
    """Convierte un diccionario plano o anidado básico a XML UTF-8."""
    root = ET.Element(root_tag)
    for k, v in data.items():
        child = ET.SubElement(root, k)
        if isinstance(v, (dict, list)):
            child.text = json.dumps(v)
        else:
            child.text = str(v)
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)

def deserialize_xml_to_dict(xml_bytes: bytes) -> Tuple[str, Dict[str, Any]]:
    """Deserializa XML UTF-8 a un diccionario de Python. Retorna (tag_raiz, dict_datos)."""
    root = ET.fromstring(xml_bytes)
    res = {}
    for child in root:
        val = child.text
        if val is None:
            res[child.tag] = None
            continue
        val = val.strip()
        # Intentar inferir enteros o floats
        if val.isdigit():
            res[child.tag] = int(val)
        else:
            try:
                res[child.tag] = float(val)
            except ValueError:
                if (val.startswith('{') and val.endswith('}')) or (val.startswith('[') and val.endswith(']')):
                    try:
                        res[child.tag] = json.loads(val)
                    except Exception:
                        res[child.tag] = val
                else:
                    res[child.tag] = val
    return root.tag, res

def serialize_message(data: Dict[str, Any], format_type: str = "json", root_tag: str = "request") -> bytes:
    """Serializa un diccionario según el formato solicitado ('json' o 'xml')."""
    fmt = format_type.lower()
    if fmt == "json":
        return json.dumps(data, ensure_ascii=False).encode('utf-8')
    elif fmt == "xml":
        return serialize_dict_to_xml(data, root_tag=root_tag)
    else:
        raise ValueError(f"Formato de serialización no soportado: {format_type}")

def deserialize_message(raw_bytes: bytes, format_type: str = "json") -> Tuple[str, Dict[str, Any]]:
    """Deserializa bytes a diccionario."""
    fmt = format_type.lower()
    if fmt == "json":
        data = json.loads(raw_bytes.decode('utf-8'))
        return "json", data
    elif fmt == "xml":
        return deserialize_xml_to_dict(raw_bytes)
    else:
        raise ValueError(f"Formato no soportado: {format_type}")


# -------------------------------------------------------------
# 3. Validación de Esquemas (Fase 3 - Activity 1)
# -------------------------------------------------------------
def validate_json_request(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Valida una solicitud JSON contra schemas/request.schema.json."""
    if _REQUEST_JSON_SCHEMA is None:
        load_schemas()
    try:
        jsonschema.validate(instance=data, schema=_REQUEST_JSON_SCHEMA)
        return True, None
    except jsonschema.ValidationError as e:
        return False, e.message

def validate_json_response(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Valida una respuesta JSON contra schemas/response.schema.json."""
    if _RESPONSE_JSON_SCHEMA is None:
        load_schemas()
    try:
        jsonschema.validate(instance=data, schema=_RESPONSE_JSON_SCHEMA)
        return True, None
    except jsonschema.ValidationError as e:
        return False, e.message

def validate_xml_message(xml_bytes: bytes) -> Tuple[bool, Optional[str]]:
    """Valida un mensaje XML contra schemas/message.xsd."""
    if _XML_SCHEMA_VALIDATOR is None:
        load_schemas()
    try:
        doc = etree.fromstring(xml_bytes)
        _XML_SCHEMA_VALIDATOR.assertValid(doc)
        return True, None
    except etree.DocumentInvalid as e:
        return False, str(e)
    except Exception as e:
        return False, f"XML sintaxis inválida: {str(e)}"


# -------------------------------------------------------------
# 4. Validación Programática en Código (Fase 3 - Activity 2)
# -------------------------------------------------------------
def validate_training_report_programmatic(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validación en código sin esquemas externos para el servicio 'training_report'.
    Reglas:
    - client_id no vacío y debe ser 'client_1' o 'client_2'.
    - round debe ser entero >= 0.
    - samples debe ser entero > 0.
    - local_loss debe ser numérico finito >= 0.
    """
    client_id = data.get("client_id")
    if not client_id or not isinstance(client_id, str) or client_id not in ["client_1", "client_2"]:
        return False, f"client_id inválido o vacío: '{client_id}'. Debe ser 'client_1' o 'client_2'."

    round_num = data.get("round")
    if round_num is None or not isinstance(round_num, int) or round_num < 0:
        return False, f"round debe ser un entero positivo o cero, valor recibido: {round_num}"

    samples = data.get("samples")
    if samples is None or not isinstance(samples, int) or samples <= 0:
        return False, f"samples debe ser un entero > 0, valor recibido: {samples}"

    local_loss = data.get("local_loss")
    if local_loss is None or not isinstance(local_loss, (int, float)) or local_loss < 0 or local_loss != local_loss: # NaN check
        return False, f"local_loss debe ser un valor numérico real no negativo, valor recibido: {local_loss}"

    return True, None
