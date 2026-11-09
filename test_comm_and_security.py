"""
Script de verificación para Fase 2 (TCP sockets), Fase 3 (JSON y XML) y Fase 4 (Cifrado Fernet).
"""

import time
import threading
from client.encryption import ClientSecurityManager
from server.encryption import ServerSecurityManager
from server.communication import ServerCommunication
from client.communication import ClientCommunication

def run_tests():
    print("=" * 60)
    print("INICIANDO PRUEBAS DE COMUNICACIÓN, ESQUEMAS Y SEGURIDAD")
    print("=" * 60)

    # 1. Configurar claves Fernet independientes
    c1_sec = ClientSecurityManager("client_1")
    c2_sec = ClientSecurityManager("client_2")

    srv_sec = ServerSecurityManager()
    srv_sec.register_client_key("client_1", c1_sec.get_key())
    srv_sec.register_client_key("client_2", c2_sec.get_key())

    # Handler del servidor para solicitudes
    def mock_server_handler(req_data, client_addr):
        service = req_data.get("service")
        round_num = req_data.get("round", 0)
        cid = req_data.get("client_id", "unknown")

        if service == "get_global_model":
            return {
                "status": "success",
                "round": round_num,
                "model_version": round_num,
                "message": "Global model delivered",
                "client_id": cid
            }
        elif service == "training_report":
            return {
                "status": "received",
                "round": round_num,
                "message": f"Reporte de {cid} registrado",
                "client_id": cid
            }
        else:
            return {"status": "error", "round": round_num, "message": "Servicio desconocido"}

    # -------------------------------------------------------------
    # PRUEBA A: Servidor en texto claro (JSON y XML)
    # -------------------------------------------------------------
    print("\n--- PRUEBA A: Comunicación en texto claro (JSON y XML) ---")
    server_plain = ServerCommunication(host="127.0.0.1", port=5555, use_encryption=False)
    server_plain.start(mock_server_handler)
    time.sleep(0.5)

    client1_plain = ClientCommunication(server_host="127.0.0.1", server_port=5555, client_id="client_1", use_encryption=False)
    client2_plain = ClientCommunication(server_host="127.0.0.1", server_port=5555, client_id="client_2", use_encryption=False)

    # 1. Cliente 1 solicita modelo en JSON (validado por JSON Schema)
    req_json = {"client_id": "client_1", "service": "get_global_model", "round": 1, "format": "json"}
    resp1, m1 = client1_plain.send_request(req_json, format_type="json")
    print(f"[Cliente 1 JSON]: Status={resp1.get('status')} | RTT={m1['round_trip_time_ms']:.2f}ms | Bytes={m1['bytes_sent']}")
    assert resp1["status"] == "success", "Fallo en solicitud JSON"

    # 2. Cliente 2 solicita modelo en XML (validado por XSD)
    req_xml = {"client_id": "client_2", "service": "get_global_model", "round": 1, "format": "xml"}
    resp2, m2 = client2_plain.send_request(req_xml, format_type="xml")
    print(f"[Cliente 2 XML]: Status={resp2.get('status')} | RTT={m2['round_trip_time_ms']:.2f}ms | Bytes={m2['bytes_sent']}")
    assert resp2["status"] == "success", "Fallo en solicitud XML"

    # 3. Reporte de entrenamiento (validación programática en código)
    req_rep = {"client_id": "client_1", "service": "training_report", "round": 1, "samples": 3000, "local_loss": 0.045}
    resp3, _ = client1_plain.send_request(req_rep, format_type="json")
    print(f"[Reporte de entrenamiento válido]: Status={resp3.get('status')} | Msg={resp3.get('message')}")
    assert resp3["status"] == "received", "Fallo en training_report"

    # 4. Reporte inválido (samples negativo o tipo incorrecto)
    req_rep_bad = {"client_id": "client_1", "service": "training_report", "round": 1, "samples": -10, "local_loss": 0.045}
    resp_bad, _ = client1_plain.send_request(req_rep_bad, format_type="json")
    print(f"[Reporte inválido rechazado]: Status={resp_bad.get('status')} | Msg={resp_bad.get('message')}")
    assert resp_bad["status"] == "error", "Servidor no rechazó reporte inválido"

    client1_plain.close()
    client2_plain.close()
    server_plain.stop()
    time.sleep(0.5)

    # -------------------------------------------------------------
    # PRUEBA B: Servidor con cifrado simétrico Fernet
    # -------------------------------------------------------------
    print("\n--- PRUEBA B: Comunicación Cifrada con Fernet ---")
    server_enc = ServerCommunication(
        host="127.0.0.1", port=5556,
        security_manager=srv_sec, use_encryption=True
    )
    server_enc.start(mock_server_handler)
    time.sleep(0.5)

    client1_enc = ClientCommunication(
        server_host="127.0.0.1", server_port=5556,
        client_id="client_1", security_manager=c1_sec, use_encryption=True
    )
    client2_enc = ClientCommunication(
        server_host="127.0.0.1", server_port=5556,
        client_id="client_2", security_manager=c2_sec, use_encryption=True
    )

    resp_enc1, m_enc1 = client1_enc.send_request(req_json, format_type="json")
    print(f"[Cliente 1 Cifrado JSON]: Status={resp_enc1.get('status')} | EncTime={m_enc1['encryption_time_ms']:.3f}ms | Bytes={m_enc1['bytes_sent']}")
    assert resp_enc1["status"] == "success", "Fallo en cifrado Cliente 1"

    resp_enc2, m_enc2 = client2_enc.send_request(req_xml, format_type="xml")
    print(f"[Cliente 2 Cifrado XML]: Status={resp_enc2.get('status')} | EncTime={m_enc2['encryption_time_ms']:.3f}ms | Bytes={m_enc2['bytes_sent']}")
    assert resp_enc2["status"] == "success", "Fallo en cifrado Cliente 2"

    # Verificar que el tamaño cifrado es mayor por el IV, padding y HMAC de Fernet
    assert m_enc1['bytes_sent'] > m1['bytes_sent'], "El payload cifrado debe incluir overhead de Fernet"

    client1_enc.close()
    client2_enc.close()
    server_enc.stop()

    print("\n" + "=" * 60)
    print("TODAS LAS PRUEBAS DE FASE 2, 3 Y 4 PASARON SATISFACTORIAMENTE")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
