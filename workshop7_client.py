"""
Workshop 7: Cliente de Servicios Distribuidos (JSON/XML)
Sistemas Distribuidos - Semestre II 2026 - Prof. Francisco Hidrobo

Este componente corresponde a un Nodo Cliente (Nodo 1: PC o Nodo 2: Raspberry Pi).
Se conecta mediante sockets TCP al Servidor Coordinador (Nodo 0) y ejecuta:
- Actividad 1: Servicio 'get_global_model' con esquemas predefinidos (JSON Schema y XML XSD)
- Actividad 2: Servicio 'training_report' sin esquema predefinido (validación programática en código)
- Pruebas de control de rechazo ante esquemas y datos corruptos
- Medición exhaustiva de: bytes transferidos, latencia RTT y sobrecarga de procesamiento (serialización, validación, deserialización).
"""

import sys
import os
import time
import socket
import argparse
import pandas as pd
from typing import Dict, Any, Tuple

from protocol import (
    send_frame, recv_frame,
    serialize_message, deserialize_message,
    validate_json_request, validate_json_response,
    validate_xml_message, validate_training_report_programmatic
)

def run_service_call(
    sock: socket.socket,
    request_data: Dict[str, Any],
    format_type: str,
    validate_schema: bool = True
) -> Dict[str, Any]:
    """
    Ejecuta una llamada completa al servicio, registrando mediciones precisas de:
    - Serialización
    - Validación de esquema en cliente
    - Latencia RTT
    - Bytes transferidos (ida y vuelta)
    - Deserialización
    - Validación de respuesta
    """
    metrics = {
        "format": format_type.upper(),
        "bytes_sent": 0,
        "bytes_received": 0,
        "serialization_time_ms": 0.0,
        "client_val_req_time_ms": 0.0,
        "client_val_resp_time_ms": 0.0,
        "rtt_latency_ms": 0.0,
        "deserialization_time_ms": 0.0,
        "total_overhead_ms": 0.0,
        "client_req_valid": False,
        "server_resp_valid": False,
        "status": "unknown"
    }

    # 1. Serialización del mensaje
    t0 = time.perf_counter()
    raw_bytes = serialize_message(request_data, format_type=format_type, root_tag="request")
    metrics["serialization_time_ms"] = (time.perf_counter() - t0) * 1000.0
    metrics["bytes_sent"] = len(raw_bytes)

    # 2. Validación de la solicitud antes de transmitir
    t1 = time.perf_counter()
    if validate_schema:
        if format_type.lower() == "json":
            is_valid, err = validate_json_request(request_data)
        else:
            is_valid, err = validate_xml_message(raw_bytes)
    else:
        # Validación en código (Actividad 2)
        is_valid, err = validate_training_report_programmatic(request_data)
    metrics["client_val_req_time_ms"] = (time.perf_counter() - t1) * 1000.0
    metrics["client_req_valid"] = is_valid
    metrics["client_req_err"] = err

    # 3. Transmisión TCP y medición de RTT
    t_start_rtt = time.perf_counter()
    send_frame(sock, raw_bytes)
    resp_bytes = recv_frame(sock)
    metrics["rtt_latency_ms"] = (time.perf_counter() - t_start_rtt) * 1000.0

    if resp_bytes is None:
        metrics["status"] = "connection_lost"
        return metrics, None

    metrics["bytes_received"] = len(resp_bytes)

    # 4. Deserialización de la respuesta
    t2 = time.perf_counter()
    _, resp_data = deserialize_message(resp_bytes, format_type=format_type)
    metrics["deserialization_time_ms"] = (time.perf_counter() - t2) * 1000.0
    metrics["status"] = resp_data.get("status", "unknown")

    # 5. Validación de la respuesta del servidor
    t3 = time.perf_counter()
    if validate_schema:
        if format_type.lower() == "json":
            resp_valid, resp_err = validate_json_response(resp_data)
        else:
            resp_valid, resp_err = validate_xml_message(resp_bytes)
    else:
        resp_valid = True if resp_data.get("status") in ["received", "success", "error"] else False
        resp_err = None
    metrics["client_val_resp_time_ms"] = (time.perf_counter() - t3) * 1000.0
    metrics["server_resp_valid"] = resp_valid
    metrics["server_resp_err"] = resp_err

    # Sobrecarga total de procesamiento del cliente
    metrics["total_overhead_ms"] = (
        metrics["serialization_time_ms"] +
        metrics["client_val_req_time_ms"] +
        metrics["deserialization_time_ms"] +
        metrics["client_val_resp_time_ms"]
    )

    return metrics, resp_data


def run_workshop7_client(server_host: str = "127.0.0.1", server_port: int = 5000, client_id: str = "client_1"):
    print("=" * 80)
    print("CLIENTE DISTRIBUIDO - WORKSHOP 7: INTERCAMBIO JSON Y XML")
    print(f"Conectando a Servidor Coordinador en: {server_host}:{server_port}")
    print(f"Identificador del Cliente: {client_id}")
    print("=" * 80)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(15.0)
        sock.connect((server_host, server_port))
    except Exception as e:
        print(f"ERROR: No se pudo conectar al servidor en {server_host}:{server_port}: {e}")
        return

    all_metrics = []

    try:
        # =========================================================================
        # ACTIVIDAD 1: Servicio CON Esquemas Predefinidos ('get_global_model')
        # =========================================================================
        print("\n" + "#" * 80)
        print("ACTIVIDAD 1: Servicio CON Esquemas Predefinidos ('get_global_model')")
        print("Esquemas: schemas/request.schema.json, response.schema.json, message.xsd")
        print("#" * 80)

        # 1.1 JSON con JSON Schema
        print("\n[Paso 1.1] Transmisión en formato JSON:")
        req_json = {
            "client_id": client_id,
            "service": "get_global_model",
            "round": 1,
            "format": "json"
        }
        m1, r1 = run_service_call(sock, req_json, format_type="json", validate_schema=True)
        print(f"  * Solicitud enviada: {req_json}")
        print(f"  * Validación previa solicitud (JSON Schema): {'VÁLIDA (PASS)' if m1['client_req_valid'] else 'ERROR: ' + str(m1['client_req_err'])}")
        print(f"  * Respuesta recibida: {r1}")
        print(f"  * Validación respuesta (Response Schema): {'VÁLIDA (PASS)' if m1['server_resp_valid'] else 'ERROR: ' + str(m1['server_resp_err'])}")
        print(f"  * Bytes: Solicitud={m1['bytes_sent']} B | Respuesta={m1['bytes_received']} B | Total={m1['bytes_sent'] + m1['bytes_received']} B")
        print(f"  * Latencia RTT: {m1['rtt_latency_ms']:.3f} ms")
        print(f"  * Sobrecarga procesamiento: Ser={m1['serialization_time_ms']:.3f} ms | ValReq={m1['client_val_req_time_ms']:.3f} ms | Deser={m1['deserialization_time_ms']:.3f} ms | ValResp={m1['client_val_resp_time_ms']:.3f} ms | Total={m1['total_overhead_ms']:.3f} ms")
        
        m1["Actividad"] = "Actividad 1 (JSON con Schema)"
        m1["Servicio"] = "get_global_model"
        all_metrics.append(m1)

        # 1.2 XML con XSD
        print("\n[Paso 1.2] Transmisión en formato XML:")
        req_xml = {
            "client_id": client_id,
            "service": "get_global_model",
            "round": 1,
            "format": "xml"
        }
        m2, r2 = run_service_call(sock, req_xml, format_type="xml", validate_schema=True)
        print(f"  * Solicitud enviada: {req_xml}")
        print(f"  * Validación previa solicitud (XML XSD): {'VÁLIDA (PASS)' if m2['client_req_valid'] else 'ERROR: ' + str(m2['client_req_err'])}")
        print(f"  * Respuesta recibida: {r2}")
        print(f"  * Validación respuesta (XML XSD): {'VÁLIDA (PASS)' if m2['server_resp_valid'] else 'ERROR: ' + str(m2['server_resp_err'])}")
        print(f"  * Bytes: Solicitud={m2['bytes_sent']} B | Respuesta={m2['bytes_received']} B | Total={m2['bytes_sent'] + m2['bytes_received']} B")
        print(f"  * Latencia RTT: {m2['rtt_latency_ms']:.3f} ms")
        print(f"  * Sobrecarga procesamiento: Ser={m2['serialization_time_ms']:.3f} ms | ValReq={m2['client_val_req_time_ms']:.3f} ms | Deser={m2['deserialization_time_ms']:.3f} ms | ValResp={m2['client_val_resp_time_ms']:.3f} ms | Total={m2['total_overhead_ms']:.3f} ms")

        m2["Actividad"] = "Actividad 1 (XML con XSD)"
        m2["Servicio"] = "get_global_model"
        all_metrics.append(m2)

        # 1.3 Prueba de Control: Violación de Esquema
        print("\n[Paso 1.3] Caso de Control Negativo (Payload corrupto violando esquema):")
        bad_req = {
            "client_id": "nodo_no_autorizado_99",
            "service": "get_global_model",
            "round": -5,
            "format": "json"
        }
        print(f"  * Enviando solicitud deliberadamente inválida: {bad_req}")
        val_bad_ok, val_bad_err = validate_json_request(bad_req)
        print(f"  * Detección local por JSON Schema: {'PASS' if val_bad_ok else 'DETECTADO (OK): ' + str(val_bad_err)}")
        
        # Enviar al servidor para verificar rechazo del lado del servidor
        raw_bad = serialize_message(bad_req, format_type="json")
        send_frame(sock, raw_bad)
        resp_bad_bytes = recv_frame(sock)
        _, resp_bad_data = deserialize_message(resp_bad_bytes, format_type="json")
        print(f"  * Respuesta del servidor ante payload corrupto: {resp_bad_data}")
        assert resp_bad_data["status"] == "error", "El servidor debía rechazar la solicitud inválida"
        print("  -> Rechazo verificado correctamente por el Servidor.")

        # =========================================================================
        # ACTIVIDAD 2: Servicio SIN Esquemas Predefinidos ('training_report')
        # =========================================================================
        print("\n" + "#" * 80)
        print("ACTIVIDAD 2: Servicio SIN Esquemas Predefinidos ('training_report')")
        print("Validación: Reglas semánticas programáticas en código de aplicación")
        print("#" * 80)

        # 2.1 JSON sin esquema (Validación en código)
        print("\n[Paso 2.1] Reporte de entrenamiento válido:")
        req_rep = {
            "client_id": client_id,
            "service": "training_report",
            "round": 1,
            "samples": 3450,
            "local_loss": 0.0385,
            "format": "json"
        }
        m3, r3 = run_service_call(sock, req_rep, format_type="json", validate_schema=False)
        print(f"  * Solicitud enviada: {req_rep}")
        print(f"  * Validación en código (Reglas semánticas): {'APROBADA (PASS)' if m3['client_req_valid'] else 'ERROR: ' + str(m3['client_req_err'])}")
        print(f"  * Respuesta recibida del servidor: {r3}")
        print(f"  * Bytes: Solicitud={m3['bytes_sent']} B | Respuesta={m3['bytes_received']} B | Total={m3['bytes_sent'] + m3['bytes_received']} B")
        print(f"  * Latencia RTT: {m3['rtt_latency_ms']:.3f} ms")
        print(f"  * Sobrecarga procesamiento: Ser={m3['serialization_time_ms']:.3f} ms | ValCódigo={m3['client_val_req_time_ms']:.3f} ms | Deser={m3['deserialization_time_ms']:.3f} ms | Total={m3['total_overhead_ms']:.3f} ms")

        m3["Actividad"] = "Actividad 2 (Sin Schema / Código)"
        m3["Servicio"] = "training_report"
        all_metrics.append(m3)

        # 2.2 Prueba de Control: Violación de Reglas Semánticas en código
        print("\n[Paso 2.2] Caso de Control Negativo (Regla semántica violada: samples <= 0):")
        bad_rep = {
            "client_id": client_id,
            "service": "training_report",
            "round": 1,
            "samples": -450,
            "local_loss": 0.0385,
            "format": "json"
        }
        print(f"  * Enviando reporte con muestras negativas: {bad_rep}")
        val_code_ok, val_code_err = validate_training_report_programmatic(bad_rep)
        print(f"  * Detección por validador programático: {'PASS' if val_code_ok else 'DETECTADO (OK): ' + str(val_code_err)}")

        raw_bad_rep = serialize_message(bad_rep, format_type="json")
        send_frame(sock, raw_bad_rep)
        resp_bad_rep_bytes = recv_frame(sock)
        _, resp_bad_rep_data = deserialize_message(resp_bad_rep_bytes, format_type="json")
        print(f"  * Respuesta del servidor: {resp_bad_rep_data}")
        assert resp_bad_rep_data["status"] == "error", "El servidor debía rechazar datos semánticamente ilógicos"
        print("  -> Rechazo semántico verificado con éxito por el Servidor.")

        # =========================================================================
        # TABLA COMPARATIVA DE RESULTADOS EXPERIMENTALES
        # =========================================================================
        print("\n" + "=" * 80)
        print("TABLA COMPARATIVA FINAL DE RENDIMIENTO - WORKSHOP 7")
        print("=" * 80)

        df = pd.DataFrame([
            {
                "Actividad": m["Actividad"],
                "Servicio": m["Servicio"],
                "Formato": m["format"],
                "Bytes Solicitud": m["bytes_sent"],
                "Bytes Respuesta": m["bytes_received"],
                "Bytes Total": m["bytes_sent"] + m["bytes_received"],
                "RTT Latencia (ms)": round(m["rtt_latency_ms"], 3),
                "Serialización (ms)": round(m["serialization_time_ms"], 4),
                "Validación Req (ms)": round(m["client_val_req_time_ms"], 4),
                "Deserialización (ms)": round(m["deserialization_time_ms"], 4),
                "Overhead Total (ms)": round(m["total_overhead_ms"], 4)
            }
            for m in all_metrics
        ])

        print(df.to_string(index=False))

        # Guardar resultados en CSV
        os.makedirs("results/communication", exist_ok=True)
        csv_path = "results/communication/workshop7_measurements.csv"
        df.to_csv(csv_path, index=False)
        print(f"\n[OK] Mediciones exportadas exitosamente a: {csv_path}")

    finally:
        sock.close()
        print("\n" + "=" * 80)
        print("EJECUCIÓN DEL CLIENTE WORKSHOP 7 FINALIZADA")
        print("=" * 80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cliente Workshop 7")
    parser.add_argument("--server-host", default="127.0.0.1", help="Dirección IP o Host del Servidor")
    parser.add_argument("--port", type=int, default=5000, help="Puerto TCP del Servidor")
    parser.add_argument("--client-id", default="client_1", help="ID del cliente ('client_1' o 'client_2')")
    args = parser.parse_args()

    run_workshop7_client(server_host=args.server_host, server_port=args.port, client_id=args.client_id)
