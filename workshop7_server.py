"""


Este componente corresponde al Servidor Coordinador (Nodo 0) en la arquitectura distribuida.
Ofrece dos servicios de red:
1. 'get_global_model' (Actividad 1): Validación obligatoria mediante esquemas formales
   - JSON: schemas/request.schema.json y schemas/response.schema.json
   - XML: schemas/message.xsd
2. 'training_report' (Actividad 2): Validación programática en código sin esquema predefinido
   - Reglas semánticas en Python (samples > 0, local_loss >= 0, client_id válido)
"""

import sys
import os
import time
import socket
import argparse
import logging
from typing import Dict, Any

from protocol import (
    recv_frame, send_frame,
    serialize_message, deserialize_message,
    validate_json_request, validate_json_response,
    validate_xml_message, validate_training_report_programmatic
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("Workshop7Server")

def process_service_request(req_data: Dict[str, Any], raw_bytes: bytes, format_type: str, client_addr: str) -> Dict[str, Any]:
    """
    Despacha la solicitud entrante al servicio correspondiente y valida según la actividad.
    """
    service = req_data.get("service")
    client_id = req_data.get("client_id", "desconocido")
    round_num = req_data.get("round", 0)

    # -------------------------------------------------------------
    # ACTIVIDAD 1: Servicio CON Esquema Predefinido ('get_global_model')
    # -------------------------------------------------------------
    if service == "get_global_model":
        logger.info(f"[{client_addr}] [ACTIVIDAD 1] Solicitud recibida: 'get_global_model' (Formato: {format_type.upper()})")
        
        # Validación de esquema en el Servidor
        t0 = time.perf_counter()
        if format_type == "json":
            is_valid, err_msg = validate_json_request(req_data)
        elif format_type == "xml":
            is_valid, err_msg = validate_xml_message(raw_bytes)
        else:
            is_valid, err_msg = False, f"Formato desconocido: {format_type}"
        val_time = (time.perf_counter() - t0) * 1000.0

        if not is_valid:
            logger.warning(f"[{client_addr}] Validación de esquema FALLÓ ({val_time:.3f} ms): {err_msg}")
            return {
                "status": "error",
                "round": round_num,
                "message": f"Esquema inválido: {err_msg}",
                "client_id": client_id
            }

        logger.info(f"[{client_addr}] Validación de esquema EXITOSA ({val_time:.3f} ms). Generando respuesta...")
        
        response_payload = {
            "status": "success",
            "round": round_num,
            "model_version": round_num,
            "message": f"Modelo global ronda {round_num} entregado con éxito a {client_id}",
            "client_id": client_id
        }

        # Validar la respuesta del servidor contra su propio esquema si es JSON
        if format_type == "json":
            resp_valid, resp_err = validate_json_response(response_payload)
            if not resp_valid:
                logger.error(f"Error interno: la respuesta no cumple response.schema.json: {resp_err}")

        return response_payload

    # -------------------------------------------------------------
    # ACTIVIDAD 2: Servicio SIN Esquema Predefinido ('training_report')
    # -------------------------------------------------------------
    elif service == "training_report":
        logger.info(f"[{client_addr}] [ACTIVIDAD 2] Solicitud recibida: 'training_report' (Sin esquema, validación en código)")

        # Validación semántica programática directa en código
        t0 = time.perf_counter()
        is_valid, err_msg = validate_training_report_programmatic(req_data)
        val_time = (time.perf_counter() - t0) * 1000.0

        if not is_valid:
            logger.warning(f"[{client_addr}] Validación en código RECHAZADA ({val_time:.3f} ms): {err_msg}")
            return {
                "status": "error",
                "round": round_num,
                "message": f"Validación programática falló: {err_msg}",
                "client_id": client_id
            }

        logger.info(f"[{client_addr}] Validación en código APROBADA ({val_time:.3f} ms). Muestras={req_data.get('samples')}, Loss={req_data.get('local_loss')}")
        return {
            "status": "received",
            "round": round_num,
            "message": f"Reporte de entrenamiento de {client_id} (Ronda {round_num}) persistido correctamente",
            "client_id": client_id
        }

    else:
        logger.warning(f"[{client_addr}] Servicio no reconocido: '{service}'")
        return {
            "status": "error",
            "round": round_num,
            "message": f"Servicio '{service}' no soportado por este componente",
            "client_id": client_id
        }


def run_server(host: str = "0.0.0.0", port: int = 5000):
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((host, port))
    server_sock.listen(5)

    print("=" * 80)
    print("SERVIDOR COORDINADOR (NODO 0) - INTERCAMBIO JSON / XML")
    print(f"Dirección de escucha: {host}:{port}")
    print("Servicios disponibles:")
    print("  1. 'get_global_model' (1 - Con JSON Schema y XML XSD)")
    print("  2. 'training_report'  (2 - Validación semántica en código)")
    print("Esperando conexiones entrantes de clientes distribuidos...")
    print("=" * 80)

    try:
        while True:
            client_sock, client_addr = server_sock.accept()
            client_str = f"{client_addr[0]}:{client_addr[1]}"
            logger.info(f"Nueva conexión establecida desde {client_str}")

            try:
                while True:
                    frame = recv_frame(client_sock)
                    if frame is None:
                        logger.info(f"Cliente {client_str} desconectado.")
                        break

                    # Detectar si es JSON o XML por el primer byte no blanco
                    first_char = frame.strip()[:1]
                    format_type = "xml" if first_char == b'<' else "json"

                    # Deserializar
                    t_deser_0 = time.perf_counter()
                    _, req_dict = deserialize_message(frame, format_type=format_type)
                    t_deser = (time.perf_counter() - t_deser_0) * 1000.0

                    # Procesar y obtener respuesta
                    resp_dict = process_service_request(req_dict, frame, format_type, client_str)

                    # Serializar respuesta en el mismo formato
                    t_ser_0 = time.perf_counter()
                    resp_bytes = serialize_message(resp_dict, format_type=format_type, root_tag="response")
                    t_ser = (time.perf_counter() - t_ser_0) * 1000.0

                    # Enviar trama
                    send_frame(client_sock, resp_bytes)
                    logger.info(f"[{client_str}] Respuesta enviada: {len(resp_bytes)} bytes (Ser: {t_ser:.3f} ms, Deser req: {t_deser:.3f} ms)")

            except ConnectionResetError:
                logger.info(f"Conexión reiniciada abruptamente por {client_str}")
            except Exception as e:
                logger.error(f"Error atendiendo a {client_str}: {e}")
            finally:
                client_sock.close()

    except KeyboardInterrupt:
        print("\nServidor detenido por el usuario.")
    finally:
        server_sock.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Servidor Workshop 7")
    parser.add_argument("--host", default="0.0.0.0", help="Host o IP de escucha (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5000, help="Puerto TCP (default: 5000)")
    args = parser.parse_args()

    run_server(host=args.host, port=args.port)
