"""
Demostración local completa del Sistema Distribuido con Cifrado Fernet.
Ejecuta el Servidor Coordinador y los dos Clientes (client_1 y client_2)
en hilos concurrentes sobre la interfaz de red local (127.0.0.1:5000).
"""

import sys
import os
import time
import threading
import argparse

# Asegurar path base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from server.server import FederatedServer
from client.client import FederatedClient

def run_local_demo(rounds: int = 2, use_encryption: bool = True, format_type: str = "json", port: int = 5000):
    print("=" * 70)
    print("  INICIANDO DEMOSTRACIÓN COMPLETA DEL SISTEMA DISTRIBUIDO")
    print(f"  Rondas: {rounds} | Cifrado Fernet: {use_encryption} | Formato: {format_type.upper()}")
    print("=" * 70)

    # 1. Instanciar Servidor
    server = FederatedServer(
        host="127.0.0.1",
        port=port,
        total_rounds=rounds,
        min_clients=2,
        use_encryption=use_encryption,
        preferred_format=format_type,
        round_timeout=25.0,
        restore_checkpoint=False
    )

    server_thread = threading.Thread(target=server.start, name="ServerThread", daemon=True)
    server_thread.start()
    time.sleep(1.0)  # Esperar que el socket del servidor se abra

    # 2. Funciones para los clientes
    def client_worker(cid: str, dist: str):
        c = FederatedClient(
            client_id=cid,
            server_host="127.0.0.1",
            server_port=port,
            distribution_type=dist,
            use_encryption=use_encryption,
            preferred_format=format_type,
            local_epochs=2,
            batch_size=32
        )
        c.run_rounds(total_rounds=rounds)

    c1_thread = threading.Thread(target=client_worker, args=("client_1", "iid"), name="Client1Thread")
    c2_thread = threading.Thread(target=client_worker, args=("client_2", "iid"), name="Client2Thread")

    # Iniciar clientes en paralelo
    c1_thread.start()
    c2_thread.start()

    # Esperar que terminen los clientes y el servidor
    c1_thread.join()
    c2_thread.join()
    server_thread.join(timeout=10.0)

    print("\n" + "=" * 70)
    print("  DEMOSTRACIÓN FINALIZADA CON ÉXITO")
    print("  Resumen del Entrenamiento Federado con Seguridad:")
    print("-" * 70)
    print(f"  {'Ronda':<7} | {'MAE':<10} | {'RMSE':<10} | {'Loss':<10} | {'Duración (s)':<12}")
    print("-" * 70)
    for entry in server.training_history:
        dur = entry.get('duration_sec', entry.get('duration', 0.0))
        loss = entry.get('loss', 0.0)
        print(f"  {entry.get('round', 0):<7} | {entry.get('mae', 0.0):<10.4f} | {entry.get('rmse', 0.0):<10.4f} | {loss:<10.4f} | {dur:<12.2f}")
    print("=" * 70)
    print(f"  Checkpoints guardados en: server/checkpoints/")
    print(f"  Logs generados en: server/logs/events.log y server/logs/failures.log\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demostración local del Sistema Distribuido con Seguridad")
    parser.add_argument("--rounds", type=int, default=2, help="Número de rondas a ejecutar (default: 2)")
    parser.add_argument("--no-encryption", action="store_true", help="Desactivar cifrado Fernet (por defecto está activo)")
    parser.add_argument("--format", default="json", choices=["json", "xml"], help="Formato de mensaje (json o xml)")
    parser.add_argument("--port", type=int, default=5000, help="Puerto TCP (default: 5000)")
    args = parser.parse_args()

    run_local_demo(
        rounds=args.rounds,
        use_encryption=not args.no_encryption,
        format_type=args.format,
        port=args.port
    )
