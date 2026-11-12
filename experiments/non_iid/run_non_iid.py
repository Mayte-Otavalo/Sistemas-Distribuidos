"""
Experimento E03: Aprendizaje Federado con Distribución Non-IID (Heterogeneidad Temporal).
Coordina el entrenamiento con particiones no idénticamente distribuidas.
"""

import os
import sys
import time
import threading
import pandas as pd

# Añadir raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from server.server import FederatedServer
from client.client import FederatedClient

def run_non_iid_experiment(rounds=5, port=5102, epochs=3):
    print("=" * 60)
    print("EXPERIMENTO E03: APRENDIZAJE FEDERADO NON-IID (FedAvg)")
    print("=" * 60)

    results_dir = "results/federated"
    os.makedirs(results_dir, exist_ok=True)

    # 1. Instanciar Servidor
    server = FederatedServer(
        host="127.0.0.1",
        port=port,
        total_rounds=rounds,
        min_clients=2,
        use_encryption=False,
        round_timeout=35.0
    )

    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    time.sleep(1.0)

    # 2. Instanciar Clientes con datos Non-IID
    c1 = FederatedClient(
        client_id="client_1",
        server_host="127.0.0.1",
        server_port=port,
        distribution_type="non_iid",
        use_encryption=False,
        local_epochs=epochs
    )
    c2 = FederatedClient(
        client_id="client_2",
        server_host="127.0.0.1",
        server_port=port,
        distribution_type="non_iid",
        use_encryption=False,
        local_epochs=epochs
    )

    c1_thread = threading.Thread(target=c1.run_rounds, args=(rounds,), daemon=True)
    c2_thread = threading.Thread(target=c2.run_rounds, args=(rounds,), daemon=True)

    c1_thread.start()
    c2_thread.start()

    c1_thread.join()
    c2_thread.join()
    server_thread.join(timeout=10.0)

    # 3. Guardar métricas federadas Non-IID
    df_metrics = pd.DataFrame(server.training_history)
    df_metrics.to_csv(os.path.join(results_dir, "non_iid_metrics.csv"), index=False)
    print(f"\nMétricas federadas Non-IID guardadas en {results_dir}/non_iid_metrics.csv")
    print(df_metrics[["round", "mae", "rmse", "loss", "participating_clients"]])
    return df_metrics

if __name__ == "__main__":
    run_non_iid_experiment()
