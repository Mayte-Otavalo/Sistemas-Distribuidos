"""
Experimento E04: Comparativa de Rendimiento y Sobrecarga JSON vs XML (Workshop 7).
Mide bytes transferidos, tiempo de serialización, validación, deserialización y latencia RTT.
"""

import os
import sys
import time
import pandas as pd
import numpy as np

# Añadir raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from protocol import (
    serialize_message, deserialize_message,
    validate_json_request, validate_xml_message
)
from server.global_model import AirQualityMLP, weights_to_dict
from server.communication import ServerCommunication
from client.communication import ClientCommunication

def benchmark_format(format_type: str, repetitions: int = 50, port: int = 5103):
    print(f"\n--- Ejecutando Benchmark para formato: {format_type.upper()} ({repetitions} repeticiones) ---")

    # Iniciar servidor mock
    def mock_handler(req, addr):
        return {
            "status": "success",
            "round": req.get("round", 1),
            "model_version": req.get("round", 1),
            "message": "Global model delivered",
            "client_id": req.get("client_id", "client_1")
        }

    server = ServerCommunication(host="127.0.0.1", port=port, use_encryption=False)
    server.start(mock_handler)
    time.sleep(0.5)

    client = ClientCommunication(
        server_host="127.0.0.1",
        server_port=port,
        client_id="client_1",
        use_encryption=False
    )
    client.connect()

    request_data = {
        "client_id": "client_1",
        "service": "get_global_model",
        "round": 1,
        "format": format_type
    }

    records = []

    for i in range(repetitions):
        # 1. Serialización
        t0 = time.perf_counter()
        raw_bytes = serialize_message(request_data, format_type=format_type, root_tag="request")
        t_ser = (time.perf_counter() - t0) * 1000.0

        # 2. Validación de esquema
        t1 = time.perf_counter()
        if format_type == "json":
            valid, _ = validate_json_request(request_data)
        else:
            valid, _ = validate_xml_message(raw_bytes)
        t_val = (time.perf_counter() - t1) * 1000.0

        # 3. Transmisión TCP y RTT
        resp, comm_metrics = client.send_request(request_data, format_type=format_type)

        # 4. Deserialización
        t2 = time.perf_counter()
        _, _ = deserialize_message(raw_bytes, format_type=format_type)
        t_deser = (time.perf_counter() - t2) * 1000.0

        records.append({
            "repetition": i + 1,
            "format": format_type,
            "payload_bytes": len(raw_bytes),
            "serialization_ms": t_ser,
            "validation_ms": t_val,
            "deserialization_ms": t_deser,
            "round_trip_ms": comm_metrics["round_trip_time_ms"],
            "total_processing_ms": t_ser + t_val + t_deser
        })

    client.close()
    server.stop()
    return pd.DataFrame(records)

def run_json_vs_xml_experiment(repetitions=50):
    print("=" * 60)
    print("EXPERIMENTO E04: BENCHMARKING DE PROTOCOLOS JSON VS XML")
    print("=" * 60)

    results_dir = "results/communication"
    os.makedirs(results_dir, exist_ok=True)

    json_df = benchmark_format("json", repetitions=repetitions, port=5201)
    xml_df = benchmark_format("xml", repetitions=repetitions, port=5202)

    json_df.to_csv(os.path.join(results_dir, "json_results.csv"), index=False)
    xml_df.to_csv(os.path.join(results_dir, "xml_results.csv"), index=False)

    comparison_summary = pd.DataFrame({
        "Métrica": [
            "Tamaño mensaje (Bytes)",
            "Tiempo Serialización (ms)",
            "Tiempo Validación (ms)",
            "Tiempo Deserialización (ms)",
            "Latencia RTT (ms)",
            "Overhead Procesamiento Total (ms)"
        ],
        "JSON (Promedio)": [
            json_df["payload_bytes"].mean(),
            json_df["serialization_ms"].mean(),
            json_df["validation_ms"].mean(),
            json_df["deserialization_ms"].mean(),
            json_df["round_trip_ms"].mean(),
            json_df["total_processing_ms"].mean()
        ],
        "XML (Promedio)": [
            xml_df["payload_bytes"].mean(),
            xml_df["serialization_ms"].mean(),
            xml_df["validation_ms"].mean(),
            xml_df["deserialization_ms"].mean(),
            xml_df["round_trip_ms"].mean(),
            xml_df["total_processing_ms"].mean()
        ]
    })
    
    # Calcular diferencia porcentual
    diff_pct = []
    for _, row in comparison_summary.iterrows():
        j_val = row["JSON (Promedio)"]
        x_val = row["XML (Promedio)"]
        if j_val > 0:
            diff = ((x_val - j_val) / j_val) * 100.0
        else:
            diff = 0.0
        diff_pct.append(diff)
    comparison_summary["Diferencia XML vs JSON (%)"] = diff_pct

    comp_path = os.path.join(results_dir, "comparison.csv")
    comparison_summary.to_csv(comp_path, index=False)

    print("\n" + "=" * 60)
    print("RESUMEN COMPARATIVO JSON VS XML:")
    print("=" * 60)
    print(comparison_summary.to_string(index=False))
    return comparison_summary

if __name__ == "__main__":
    run_json_vs_xml_experiment()
