"""
Script Demostrativo para el Workshop 7 (Sistemas Distribuidos).
Permite probar en una sola computadora (usando interfaz de loopback 127.0.0.1 y sockets TCP)
las dos actividades requeridas:
- Actividad 1: Servicio 'get_global_model' con esquemas predefinidos (JSON Schema y XML XSD).
- Actividad 2: Servicio 'training_report' sin esquemas predefinidos (validación programática en código).
Mide: bytes transferidos, latencia RTT y sobrecarga de procesamiento (serialización, validación, deserialización).
"""

import os
import sys
import time
import socket
import threading
import pandas as pd

from protocol import (
    serialize_message, deserialize_message,
    validate_json_request, validate_json_response,
    validate_xml_message, validate_training_report_programmatic
)
from server.communication import ServerCommunication
from client.communication import ClientCommunication

def run_workshop7_demo(port=5800):
    print("=" * 80)
    print("DEMOSTRACIÓN INTERACTIVA - WORKSHOP 7: INTERCAMBIO CON JSON Y XML")
    print("Ejecutando en 1 sola computadora mediante interfaz de red Loopback (127.0.0.1)")
    print("=" * 80)

    # 1. Definir el servidor que atiende ambos servicios
    def server_dispatcher(req_data, client_addr):
        service = req_data.get("service")
        cid = req_data.get("client_id", "desconocido")
        round_num = req_data.get("round", 1)

        if service == "get_global_model":
            # Servicio Actividad 1
            return {
                "status": "success",
                "round": round_num,
                "model_version": round_num,
                "message": "Global model delivered",
                "client_id": cid
            }
        elif service == "training_report":
            # Servicio Actividad 2
            return {
                "status": "received",
                "round": round_num,
                "message": f"Reporte local de {cid} registrado con éxito",
                "client_id": cid
            }
        else:
            return {"status": "error", "round": round_num, "message": "Servicio no soportado"}

    # Iniciar servidor TCP en un hilo de fondo (simula la Máquina Servidor)
    server = ServerCommunication(host="127.0.0.1", port=port, use_encryption=False)
    server.start(server_dispatcher)
    time.sleep(0.5)

    # Iniciar cliente TCP (simula la Máquina Cliente)
    client = ClientCommunication(server_host="127.0.0.1", server_port=port, client_id="client_1", use_encryption=False)
    client.connect()

    # -------------------------------------------------------------------------
    # ACTIVIDAD 1: Servicio con Esquemas Predefinidos (get_global_model)
    # -------------------------------------------------------------------------
    print("\n" + "#" * 80)
    print("ACTIVIDAD 1: Servicio CON Esquemas Predefinidos ('get_global_model')")
    print("Esquemas utilizados: schemas/request.schema.json, response.schema.json, message.xsd")
    print("#" * 80)

    # Caso 1.1: JSON con JSON Schema
    print("\n[Paso 1.1] Transmisión en formato JSON (Validado con JSON Schema)")
    req_json = {
        "client_id": "client_1",
        "service": "get_global_model",
        "round": 1,
        "format": "json"
    }

    # Validación previa en cliente antes de enviar
    val_ok, val_err = validate_json_request(req_json)
    print(f" -> Validación previa de la solicitud (JSON Schema): {'CORRECTA (PASS)' if val_ok else 'FALLO: ' + str(val_err)}")

    resp_json, m_json = client.send_request(req_json, format_type="json")
    
    # Validación de la respuesta recibida contra response.schema.json
    val_resp_ok, val_resp_err = validate_json_response(resp_json)
    print(f" -> Respuesta recibida del servidor: {resp_json}")
    print(f" -> Validación de la respuesta (Response JSON Schema): {'CORRECTA (PASS)' if val_resp_ok else 'FALLO: ' + str(val_resp_err)}")
    print(f" -> Mediciones:")
    print(f"    - Bytes transferidos: Solicitud={m_json['bytes_sent']} B | Respuesta={m_json['bytes_received']} B")
    print(f"    - Latencia de ida y vuelta (RTT): {m_json['round_trip_time_ms']:.2f} ms")
    print(f"    - Sobrecarga: Serialización={m_json['serialization_time_ms']:.3f} ms | Deserialización={m_json['deserialization_time_ms']:.3f} ms")

    # Caso 1.2: XML con XML Schema (XSD)
    print("\n[Paso 1.2] Transmisión en formato XML (Validado con XSD)")
    req_xml = {
        "client_id": "client_1",
        "service": "get_global_model",
        "round": 1,
        "format": "xml"
    }
    raw_xml = serialize_message(req_xml, format_type="xml", root_tag="request")
    val_xml_ok, val_xml_err = validate_xml_message(raw_xml)
    print(f" -> Validación previa de la solicitud (XML XSD): {'CORRECTA (PASS)' if val_xml_ok else 'FALLO: ' + str(val_xml_err)}")

    resp_xml, m_xml = client.send_request(req_xml, format_type="xml")
    raw_resp_xml = serialize_message(resp_xml, format_type="xml", root_tag="response")
    val_resp_xml_ok, val_resp_xml_err = validate_xml_message(raw_resp_xml)
    print(f" -> Respuesta recibida del servidor: {resp_xml}")
    print(f" -> Validación de la respuesta (XML XSD): {'CORRECTA (PASS)' if val_resp_xml_ok else 'FALLO: ' + str(val_resp_xml_err)}")
    print(f" -> Mediciones:")
    print(f"    - Bytes transferidos: Solicitud={m_xml['bytes_sent']} B | Respuesta={m_xml['bytes_received']} B")
    print(f"    - Latencia de ida y vuelta (RTT): {m_xml['round_trip_time_ms']:.2f} ms")
    print(f"    - Sobrecarga: Serialización={m_xml['serialization_time_ms']:.3f} ms | Deserialización={m_xml['deserialization_time_ms']:.3f} ms")

    # Caso 1.3: Prueba de rechazo ante violación de esquema
    print("\n[Paso 1.3] Prueba de Control: Envío de solicitud INVÁLIDA (client_id inválido 'hacker_99')")
    bad_req_json = {"client_id": "hacker_99", "service": "get_global_model", "round": 1, "format": "json"}
    bad_resp, _ = client.send_request(bad_req_json, format_type="json")
    print(f" -> Respuesta del servidor ante payload corrupto/inválido: {bad_resp}")

    # -------------------------------------------------------------------------
    # ACTIVIDAD 2: Servicio SIN Esquemas Predefinidos (training_report)
    # -------------------------------------------------------------------------
    print("\n" + "#" * 80)
    print("ACTIVIDAD 2: Servicio SIN Esquemas Predefinidos ('training_report')")
    print("Validación: Reglas semánticas programadas directamente en código Python")
    print("#" * 80)

    # Caso 2.1: Solicitud válida
    print("\n[Paso 2.1] Reporte de entrenamiento válido:")
    req_report = {
        "client_id": "client_1",
        "service": "training_report",
        "round": 1,
        "samples": 3274,
        "local_loss": 0.0412,
        "format": "json"
    }

    # Validación en código
    code_val_ok, code_val_err = validate_training_report_programmatic(req_report)
    print(f" -> Validación semántica en código: {'VÁLIDA (PASS)' if code_val_ok else 'RECHAZADA: ' + str(code_val_err)}")

    resp_rep, m_rep = client.send_request(req_report, format_type="json")
    print(f" -> Respuesta recibida del servidor: {resp_rep}")
    print(f" -> Mediciones:")
    print(f"    - Bytes transferidos: Solicitud={m_rep['bytes_sent']} B | Respuesta={m_rep['bytes_received']} B")
    print(f"    - Latencia RTT: {m_rep['round_trip_time_ms']:.2f} ms")
    print(f"    - Sobrecarga: Serialización={m_rep['serialization_time_ms']:.3f} ms | Deserialización={m_rep['deserialization_time_ms']:.3f} ms")

    # Caso 2.2: Prueba de rechazo en código (muestras negativas y client_id vacío)
    print("\n[Paso 2.2] Prueba de Control: Reporte con datos ilógicos (samples = -500)")
    bad_rep = {
        "client_id": "client_1",
        "service": "training_report",
        "round": 1,
        "samples": -500,
        "local_loss": 0.0412,
        "format": "json"
    }
    code_bad_ok, code_bad_err = validate_training_report_programmatic(bad_rep)
    print(f" -> Detección local del error: {code_bad_err}")
    resp_bad_rep, _ = client.send_request(bad_rep, format_type="json")
    print(f" -> Servidor rechazó la operación: {resp_bad_rep}")

    # -------------------------------------------------------------------------
    # TABLA COMPARATIVA DE MEDICIONES (BYTES, LATENCIA Y OVERHEAD)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("TABLA COMPARATIVA FINAL DE RENDIMIENTO (ACTIVIDADES 1 Y 2)")
    print("=" * 80)

    summary_table = pd.DataFrame([
        {
            "Actividad": "Actividad 1 (JSON con Schema)",
            "Servicio": "get_global_model",
            "Bytes Enviados": m_json["bytes_sent"],
            "Bytes Recibidos": m_json["bytes_received"],
            "Latencia RTT (ms)": round(m_json["round_trip_time_ms"], 2),
            "Serialización (ms)": round(m_json["serialization_time_ms"], 3),
            "Deserialización (ms)": round(m_json["deserialization_time_ms"], 3)
        },
        {
            "Actividad": "Actividad 1 (XML con XSD)",
            "Servicio": "get_global_model",
            "Bytes Enviados": m_xml["bytes_sent"],
            "Bytes Recibidos": m_xml["bytes_received"],
            "Latencia RTT (ms)": round(m_xml["round_trip_time_ms"], 2),
            "Serialización (ms)": round(m_xml["serialization_time_ms"], 3),
            "Deserialización (ms)": round(m_xml["deserialization_time_ms"], 3)
        },
        {
            "Actividad": "Actividad 2 (Sin Schema / Código)",
            "Servicio": "training_report",
            "Bytes Enviados": m_rep["bytes_sent"],
            "Bytes Recibidos": m_rep["bytes_received"],
            "Latencia RTT (ms)": round(m_rep["round_trip_time_ms"], 2),
            "Serialización (ms)": round(m_rep["serialization_time_ms"], 3),
            "Deserialización (ms)": round(m_rep["deserialization_time_ms"], 3)
        }
    ])

    print(summary_table.to_string(index=False))

    client.close()
    server.stop()
    print("\n" + "=" * 80)
    print("DEMOSTRACIÓN WORKSHOP 7 CONCLUIDA CON ÉXITO")
    print("=" * 80)

if __name__ == "__main__":
    run_workshop7_demo()
