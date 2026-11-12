"""
Módulo de comunicación de red para el Cliente Federado (AIR_QUALITY_DISTRIBUTED).
Gestiona conexiones TCP hacia el Servidor Coordinador, serialización, cifrado y medición de latencia.
"""

import socket
import time
import logging
from typing import Dict, Any, Optional, Tuple
from protocol import (
    send_frame, recv_frame, serialize_message, deserialize_message,
    validate_json_response, validate_xml_message
)
from client.encryption import ClientSecurityManager

logger = logging.getLogger("ClientComm")

class ClientCommunication:
    def __init__(
        self,
        server_host: str = "127.0.0.1",
        server_port: int = 5000,
        client_id: str = "client_1",
        security_manager: Optional[ClientSecurityManager] = None,
        use_encryption: bool = False,
        timeout: float = 20.0
    ):
        self.server_host = server_host
        self.server_port = server_port
        self.client_id = client_id
        self.security_manager = security_manager
        self.use_encryption = use_encryption
        self.timeout = timeout
        self.sock: Optional[socket.socket] = None

    def connect(self) -> bool:
        """Establece conexión TCP con el servidor."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)
            self.sock.connect((self.server_host, self.server_port))
            logger.info(f"[{self.client_id}] Conexión establecida con {self.server_host}:{self.server_port}")
            return True
        except Exception as e:
            logger.error(f"[{self.client_id}] Error conectando al servidor: {e}")
            self.sock = None
            return False

    def close(self):
        """Cierra el socket cliente."""
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    def send_request(
        self,
        request_data: Dict[str, Any],
        format_type: str = "json"
    ) -> Tuple[Optional[Dict[str, Any]], Dict[str, float]]:
        """
        Envía una solicitud estructurada, espera la respuesta y registra métricas de rendimiento.
        Retorna (respuesta_dict, metricas_rendimiento).
        """
        metrics = {
            "serialization_time_ms": 0.0,
            "encryption_time_ms": 0.0,
            "bytes_sent": 0,
            "bytes_received": 0,
            "round_trip_time_ms": 0.0,
            "decryption_time_ms": 0.0,
            "deserialization_time_ms": 0.0
        }

        if not self.sock:
            if not self.connect():
                return None, metrics

        # 1. Serialización
        t0 = time.perf_counter()
        raw_bytes = serialize_message(request_data, format_type, root_tag="request")
        t1 = time.perf_counter()
        metrics["serialization_time_ms"] = (t1 - t0) * 1000.0

        # 2. Cifrado Fernet si está activo
        payload = raw_bytes
        if self.use_encryption and self.security_manager:
            t_enc0 = time.perf_counter()
            payload = self.security_manager.encrypt(raw_bytes)
            t_enc1 = time.perf_counter()
            metrics["encryption_time_ms"] = (t_enc1 - t_enc0) * 1000.0

        metrics["bytes_sent"] = len(payload)

        # 3. Envío y recepción por socket TCP
        t_net0 = time.perf_counter()
        try:
            send_frame(self.sock, payload)
            resp_frame = recv_frame(self.sock)
        except (socket.timeout, ConnectionResetError, BrokenPipeError) as e:
            logger.error(f"[{self.client_id}] Error de red durante transmisión: {e}")
            self.close()
            return None, metrics
        t_net1 = time.perf_counter()
        metrics["round_trip_time_ms"] = (t_net1 - t_net0) * 1000.0

        if resp_frame is None:
            logger.warning(f"[{self.client_id}] El servidor cerró la conexión sin responder.")
            self.close()
            return None, metrics

        metrics["bytes_received"] = len(resp_frame)

        # 4. Descifrado de la respuesta si está activo
        resp_bytes = resp_frame
        if self.use_encryption and self.security_manager:
            t_dec0 = time.perf_counter()
            try:
                resp_bytes = self.security_manager.decrypt(resp_frame)
            except Exception as e:
                logger.error(f"[{self.client_id}] Error descifrando respuesta: {e}")
                return None, metrics
            t_dec1 = time.perf_counter()
            metrics["decryption_time_ms"] = (t_dec1 - t_dec0) * 1000.0

        # 5. Deserialización de la respuesta
        t_des0 = time.perf_counter()
        try:
            _, resp_dict = deserialize_message(resp_bytes, format_type)
        except Exception as e:
            logger.error(f"[{self.client_id}] Error deserializando respuesta ({format_type}): {e}")
            return None, metrics
        t_des1 = time.perf_counter()
        metrics["deserialization_time_ms"] = (t_des1 - t_des0) * 1000.0

        return resp_dict, metrics
