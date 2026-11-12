"""
Experimento E05: Impacto de la Seguridad y Cifrado Fernet en la Comunicación.
Compara mensajes en texto claro frente a mensajes cifrados con Fernet:
mide tamaño antes/después del cifrado, tiempos de cifrado, descifrado y latencia RTT.
"""

import os
import sys
import time
import pandas as pd
import numpy as np

# Añadir raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.encryption import ClientSecurityManager
from server.encryption import ServerSecurityManager
from server.communication import ServerCommunication
from client.communication import ClientCommunication

def run_encryption_experiment(repetitions=50, port_plain=5301, port_enc=5302):
    print("=" * 60)
    print("EXPERIMENTO E05: IMPACTO DE CIFRADO FERNET VS TEXTO CLARO")
    print("=" * 60)

    results_dir = "results/encryption"
    os.makedirs(results_dir, exist_ok=True)

    # 1. Configuración de claves
    c1_sec = ClientSecurityManager("client_1")
    srv_sec = ServerSecurityManager()
    srv_sec.register_client_key("client_1", c1_sec.get_key())

    def mock_handler(req, addr):
        return {
            "status": "success",
            "round": req.get("round", 1),
            "model_version": req.get("round", 1),
            "message": "Global model delivered",
            "client_id": req.get("client_id", "client_1")
        }

    # Iniciar servidor plano y servidor cifrado
    server_plain = ServerCommunication(host="127.0.0.1", port=port_plain, use_encryption=False)
    server_plain.start(mock_handler)

    server_enc = ServerCommunication(host="127.0.0.1", port=port_enc, security_manager=srv_sec, use_encryption=True)
    server_enc.start(mock_handler)
    time.sleep(0.5)

    client_plain = ClientCommunication(server_host="127.0.0.1", server_port=port_plain, client_id="client_1", use_encryption=False)
    client_plain.connect()

    client_enc = ClientCommunication(server_host="127.0.0.1", server_port=port_enc, client_id="client_1", security_manager=c1_sec, use_encryption=True)
    client_enc.connect()

    request_data = {
        "client_id": "client_1",
        "service": "get_global_model",
        "round": 1,
        "format": "json"
    }

    records = []

    for i in range(repetitions):
        # Transmisión en texto claro
        _, m_plain = client_plain.send_request(request_data, format_type="json")

        # Transmisión cifrada Fernet
        _, m_enc = client_enc.send_request(request_data, format_type="json")

        records.append({
            "repetition": i + 1,
            "plain_bytes": m_plain["bytes_sent"],
            "encrypted_bytes": m_enc["bytes_sent"],
            "overhead_bytes": m_enc["bytes_sent"] - m_plain["bytes_sent"],
            "encryption_time_ms": m_enc["encryption_time_ms"],
            "decryption_time_ms": m_enc["decryption_time_ms"],
            "rtt_plain_ms": m_plain["round_trip_time_ms"],
            "rtt_encrypted_ms": m_enc["round_trip_time_ms"],
            "security_overhead_ms": m_enc["round_trip_time_ms"] - m_plain["round_trip_time_ms"]
        })

    client_plain.close()
    client_enc.close()
    server_plain.stop()
    server_enc.stop()

    df = pd.DataFrame(records)
    csv_path = os.path.join(results_dir, "encryption_metrics.csv")
    df.to_csv(csv_path, index=False)

    print("\n" + "=" * 60)
    print("RESUMEN DE MÉTRICAS DE SEGURIDAD (FERNET):")
    print("=" * 60)
    print(f"Tamaño sin cifrar (promedio): {df['plain_bytes'].mean():.1f} bytes")
    print(f"Tamaño con Fernet (promedio): {df['encrypted_bytes'].mean():.1f} bytes (+{df['overhead_bytes'].mean():.1f} bytes)")
    print(f"Tiempo de Cifrado (promedio): {df['encryption_time_ms'].mean():.4f} ms")
    print(f"Tiempo de Descifrado (promedio): {df['decryption_time_ms'].mean():.4f} ms")
    print(f"Latencia RTT Plano (promedio): {df['rtt_plain_ms'].mean():.2f} ms")
    print(f"Latencia RTT Cifrado (promedio): {df['rtt_encrypted_ms'].mean():.2f} ms")
    print(f"Resultados exportados a: {csv_path}")
    return df

if __name__ == "__main__":
    run_encryption_experiment()
