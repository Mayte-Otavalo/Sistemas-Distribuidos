"""
Módulo de comunicación de red para el Servidor Coordinador (AIR_QUALITY_DISTRIBUTED).
Gestiona conexiones TCP entrantes, delimitación de tramas, descifrado y despacho concurrente.
"""

import socket
import threading
import logging
from typing import Callable, Optional, Dict, Any
from protocol import (
    recv_frame, send_frame, deserialize_message, serialize_message,
    validate_json_request, validate_xml_message, validate_training_report_programmatic
)
from server.encryption import ServerSecurityManager

logger = logging.getLogger("ServerComm")

class ServerCommunication:
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 5000,
        security_manager: Optional[ServerSecurityManager] = None,
        use_encryption: bool = False,
        timeout: float = 30.0
    ):
        self.host = host
        self.port = port
        self.security_manager = security_manager
        self.use_encryption = use_encryption
        self.timeout = timeout
        self.server_sock: Optional[socket.socket] = None
        self.is_running = False
        self.client_handlers: Dict[str, Callable] = {}
        self._threads = []

    def start(self, request_handler: Callable[[Dict[str, Any], str], Dict[str, Any]]):
        """
        Inicia el socket servidor y el hilo de aceptación de conexiones.
        request_handler: callback(request_dict, client_address) -> response_dict
        """
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.bind((self.host, self.port))
        self.server_sock.listen(10)
        self.is_running = True
        logger.info(f"Servidor iniciado. Escuchando en {self.host}:{self.port} (Cifrado={self.use_encryption})")

        accept_thread = threading.Thread(target=self._accept_loop, args=(request_handler,), daemon=True)
        accept_thread.start()
        self._threads.append(accept_thread)

    def _accept_loop(self, request_handler: Callable):
        while self.is_running:
            try:
                client_sock, client_addr = self.server_sock.accept()
                client_sock.settimeout(self.timeout)
                t = threading.Thread(
                    target=self._handle_client_connection,
                    args=(client_sock, client_addr, request_handler),
                    daemon=True
                )
                t.start()
                self._threads.append(t)
            except Exception as e:
                if self.is_running:
                    logger.error(f"Error aceptando conexión: {e}")
                break

    def _handle_client_connection(
        self,
        client_sock: socket.socket,
        client_addr: tuple,
        request_handler: Callable
    ):
        logger.info(f"Nueva conexión TCP desde {client_addr}")
        try:
            while self.is_running:
                frame_bytes = recv_frame(client_sock)
                if frame_bytes is None:
                    logger.info(f"Cliente en {client_addr} cerró la conexión.")
                    break

                # 1. Descifrado si está activo
                payload_bytes = frame_bytes
                client_id = None
                format_type = "json"

                if self.use_encryption:
                    # En modo cifrado con Fernet, el cliente debe identificarse o usamos clave correspondiente
                    # Si no conocemos de antemano el client_id, intentamos descifrar con cada clave conocida
                    decrypted = False
                    if self.security_manager:
                        for candidate_id in self.security_manager.ciphers:
                            try:
                                payload_bytes = self.security_manager.decrypt_for_client(candidate_id, frame_bytes)
                                client_id = candidate_id
                                decrypted = True
                                break
                            except Exception:
                                continue
                    if not decrypted:
                        logger.error(f"No se pudo descifrar el mensaje desde {client_addr}. Clave inválida o corrupto.")
                        error_resp = {"status": "error", "round": 0, "message": "Fallo de descifrado Fernet"}
                        send_frame(client_sock, serialize_message(error_resp, "json"))
                        continue

                # 2. Detección o deserialización de formato (JSON vs XML)
                try:
                    # Intentar JSON primero
                    if payload_bytes.strip().startswith(b'{'):
                        format_type = "json"
                        _, req_data = deserialize_message(payload_bytes, "json")
                    elif payload_bytes.strip().startswith(b'<'):
                        format_type = "xml"
                        _, req_data = deserialize_message(payload_bytes, "xml")
                    else:
                        format_type = "json"
                        _, req_data = deserialize_message(payload_bytes, "json")
                except Exception as e:
                    logger.error(f"Error de deserialización ({format_type}): {e}")
                    error_resp = {"status": "error", "round": 0, "message": f"Error de sintaxis {format_type}: {e}"}
                    send_frame(client_sock, serialize_message(error_resp, format_type, root_tag="response"))
                    continue

                if not client_id and "client_id" in req_data:
                    client_id = req_data["client_id"]

                # 3. Validación de esquemas según servicio
                service = req_data.get("service")
                is_valid = True
                val_error = None

                if service == "get_global_model":
                    if format_type == "json":
                        is_valid, val_error = validate_json_request(req_data)
                    else:
                        is_valid, val_error = validate_xml_message(payload_bytes)
                elif service == "training_report":
                    # Servicio 2: sin esquema externo, validación en código
                    is_valid, val_error = validate_training_report_programmatic(req_data)

                if not is_valid:
                    logger.warning(f"Mensaje inválido recibido de {client_id}: {val_error}")
                    error_resp = {
                        "status": "error",
                        "round": req_data.get("round", 0),
                        "message": f"Error de validación: {val_error}"
                    }
                    resp_bytes = serialize_message(error_resp, format_type, root_tag="response")
                    if self.use_encryption and self.security_manager and client_id:
                        resp_bytes = self.security_manager.encrypt_for_client(client_id, resp_bytes)
                    send_frame(client_sock, resp_bytes)
                    continue

                # 4. Procesar solicitud mediante el callback
                resp_data = request_handler(req_data, client_addr)
                resp_bytes = serialize_message(resp_data, format_type, root_tag="response")

                # 5. Cifrar respuesta si corresponde
                if self.use_encryption and self.security_manager and client_id:
                    resp_bytes = self.security_manager.encrypt_for_client(client_id, resp_bytes)

                send_frame(client_sock, resp_bytes)

        except socket.timeout:
            logger.warning(f"Timeout en conexión con {client_addr}")
        except ConnectionResetError:
            logger.info(f"Conexión reiniciada abruptamente por {client_addr}")
        except Exception as e:
            logger.error(f"Error atendiendo socket {client_addr}: {e}")
        finally:
            try:
                client_sock.close()
            except Exception:
                pass

    def stop(self):
        """Detiene el servidor y cierra sockets."""
        self.is_running = False
        if self.server_sock:
            try:
                self.server_sock.close()
            except Exception:
                pass
        logger.info("Servidor detenido.")
