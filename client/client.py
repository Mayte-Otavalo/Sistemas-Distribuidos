"""
Cliente Federado de Aprendizaje Automático (AIR_QUALITY_DISTRIBUTED).
Punto de entrada para Cliente 1 (PC 2) y Cliente 2 (Raspberry Pi).
Entrena localmente con datos aislados, calcula deltas y se comunica con el servidor coordinador vía TCP.
"""

import os
import sys
import time
import uuid
import argparse
import logging
from typing import Optional, Dict, Any

# Añadir directorio raíz al path para importaciones limpias
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.data_loader import get_client_dataloader
from client.local_training import LocalTrainer
from client.encryption import ClientSecurityManager
from client.communication import ClientCommunication

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("FederatedClient")

class FederatedClient:
    def __init__(
        self,
        client_id: str = "client_1",
        server_host: str = "127.0.0.1",
        server_port: int = 5000,
        distribution_type: str = "iid",
        use_encryption: bool = False,
        preferred_format: str = "json",
        local_epochs: int = 3,
        learning_rate: float = 0.005,
        batch_size: int = 32,
        max_retries: int = 5,
        retry_delay_sec: float = 3.0
    ):
        self.client_id = client_id
        self.server_host = server_host
        self.server_port = server_port
        self.distribution_type = distribution_type
        self.use_encryption = use_encryption
        self.preferred_format = preferred_format
        self.max_retries = max_retries
        self.retry_delay_sec = retry_delay_sec

        # Módulos locales
        self.trainer = LocalTrainer(
            client_id=self.client_id,
            distribution_type=self.distribution_type,
            learning_rate=learning_rate,
            local_epochs=local_epochs,
            batch_size=batch_size
        )
        self.security_manager = ClientSecurityManager(self.client_id) if self.use_encryption else None
        self.comm = ClientCommunication(
            server_host=self.server_host,
            server_port=self.server_port,
            client_id=self.client_id,
            security_manager=self.security_manager,
            use_encryption=self.use_encryption
        )

    def request_global_model_with_retry(self, round_num: int) -> Optional[Dict[str, Any]]:
        """Solicita el modelo global con reintentos exponenciales ante caídas temporales del servidor."""
        req = {
            "client_id": self.client_id,
            "service": "get_global_model",
            "round": round_num,
            "format": self.preferred_format
        }

        for attempt in range(1, self.max_retries + 1):
            resp, metrics = self.comm.send_request(req, format_type=self.preferred_format)
            if resp and resp.get("status") == "success":
                logger.info(f"[{self.client_id}] Modelo global recibido (RTT: {metrics['round_trip_time_ms']:.2f}ms, bytes: {metrics['bytes_received']})")
                return resp
            
            logger.warning(f"[{self.client_id}] Intento {attempt}/{self.max_retries} fallido al solicitar modelo global. Reintentando en {self.retry_delay_sec}s...")
            self.comm.close()
            time.sleep(self.retry_delay_sec)

        logger.error(f"[{self.client_id}] No se pudo obtener el modelo global tras {self.max_retries} intentos.")
        return None

    def send_training_report_with_retry(
        self,
        round_num: int,
        samples: int,
        loss: float,
        deltas: Dict[str, Any]
    ) -> bool:
        """Envía el reporte de entrenamiento local con ID único (idempotencia) y reintentos."""
        message_id = str(uuid.uuid4())
        req = {
            "client_id": self.client_id,
            "service": "training_report",
            "round": round_num,
            "samples": samples,
            "local_loss": float(loss),
            "deltas": deltas,
            "message_id": message_id,
            "format": self.preferred_format
        }

        for attempt in range(1, self.max_retries + 1):
            resp, metrics = self.comm.send_request(req, format_type=self.preferred_format)
            if resp and resp.get("status") == "received":
                logger.info(f"[{self.client_id}] Reporte de ronda {round_num} confirmado por el servidor (bytes: {metrics['bytes_sent']})")
                return True

            logger.warning(f"[{self.client_id}] Intento {attempt}/{self.max_retries} fallido al enviar reporte. Reintentando en {self.retry_delay_sec}s...")
            self.comm.close()
            time.sleep(self.retry_delay_sec)

        logger.error(f"[{self.client_id}] No se pudo entregar el reporte de la ronda {round_num}.")
        return False

    def run_rounds(self, total_rounds: int):
        """Ejecuta el ciclo de entrenamiento federado para el número de rondas especificado."""
        logger.info(f"=== INICIANDO CLIENTE {self.client_id} (Distribución: {self.distribution_type}, Cifrado: {self.use_encryption}, Formato: {self.preferred_format}) ===")

        last_trained_round = 0

        while last_trained_round < total_rounds:
            # 1. Consultar estado del modelo global
            model_resp = self.request_global_model_with_retry(last_trained_round + 1)
            if not model_resp:
                logger.error(f"[{self.client_id}] Servidor no disponible. Deteniendo cliente.")
                break

            current_server_round = model_resp.get("round", 0)
            global_weights = model_resp.get("weights")

            if current_server_round <= last_trained_round:
                # El servidor aún no avanza a la siguiente ronda; esperar brevemente
                time.sleep(1.0)
                continue

            target_round = current_server_round
            logger.info(f"\n[{self.client_id}] >>> Iniciando entrenamiento para Ronda Federada {target_round} / {total_rounds} <<<")

            # 2. Entrenamiento local
            t0 = time.time()
            deltas, num_samples, final_loss = self.trainer.train_round(global_weights)
            train_time = time.time() - t0

            logger.info(f"[{self.client_id}] Entrenamiento local completado ({train_time:.2f}s): {num_samples} muestras, Loss final: {final_loss:.4f}")

            # 3. Enviar deltas al servidor
            delivered = self.send_training_report_with_retry(target_round, num_samples, final_loss, deltas)
            if delivered:
                last_trained_round = target_round
            else:
                logger.error(f"[{self.client_id}] Error entregando actualización para ronda {target_round}.")
                break

            # Pequeña pausa antes de consultar siguiente ronda
            time.sleep(0.5)

        self.comm.close()
        logger.info(f"=== CLIENTE {self.client_id} HA FINALIZADO SUS RONDAS ===")

def main():
    parser = argparse.ArgumentParser(description="Cliente Federado - AIR_QUALITY_DISTRIBUTED")
    parser.add_argument("--client-id", required=True, choices=["client_1", "client_2"], help="Identificador del cliente")
    parser.add_argument("--server-host", default="127.0.0.1", help="Dirección IP del servidor coordinador")
    parser.add_argument("--server-port", type=int, default=5000, help="Puerto TCP del servidor")
    parser.add_argument("--distribution", default="iid", choices=["iid", "non_iid"], help="Tipo de distribución de datos locales")
    parser.add_argument("--rounds", type=int, default=5, help="Total de rondas a ejecutar")
    parser.add_argument("--epochs", type=int, default=3, help="Épocas locales por ronda")
    parser.add_argument("--lr", type=float, default=0.005, help="Tasa de aprendizaje (learning rate)")
    parser.add_argument("--batch-size", type=int, default=32, help="Tamaño de batch")
    parser.add_argument("--encryption", action="store_true", help="Habilitar cifrado Fernet")
    parser.add_argument("--format", default="json", choices=["json", "xml"], help="Formato de serialización (json o xml)")
    args = parser.parse_args()

    client = FederatedClient(
        client_id=args.client_id,
        server_host=args.server_host,
        server_port=args.server_port,
        distribution_type=args.distribution,
        use_encryption=args.encryption,
        preferred_format=args.format,
        local_epochs=args.epochs,
        learning_rate=args.lr,
        batch_size=args.batch_size
    )
    client.run_rounds(args.rounds)

if __name__ == "__main__":
    main()
