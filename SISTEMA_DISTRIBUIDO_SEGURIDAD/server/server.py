"""
Servidor Coordinador Centralizado para Aprendizaje Federado (AIR_QUALITY_DISTRIBUTED).
Punto de entrada principal: orquesta rondas federadas, agregación FedAvg, evaluación y tolerancia a fallos.
"""

import os
import sys
import time
import argparse
import logging
import threading
from typing import Dict, Any, List

# Añadir directorio raíz al path para importaciones limpias
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.global_model import AirQualityMLP, weights_to_dict, set_model_weights
from server.aggregation import FedAvgAggregator
from server.evaluation import ModelEvaluator
from server.fault_tolerance import FaultToleranceManager
from server.encryption import ServerSecurityManager
from server.communication import ServerCommunication
from client.encryption import ClientSecurityManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("CoordinatorServer")

class FederatedServer:
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 5000,
        total_rounds: int = 5,
        min_clients: int = 2,
        use_encryption: bool = False,
        preferred_format: str = "json",
        round_timeout: float = 30.0,
        restore_checkpoint: bool = False
    ):
        self.host = host
        self.port = port
        self.total_rounds = total_rounds
        self.min_clients = min_clients
        self.use_encryption = use_encryption
        self.preferred_format = preferred_format
        self.round_timeout = round_timeout

        # Componentes del servidor
        self.global_model = AirQualityMLP()
        self.evaluator = ModelEvaluator()
        self.fault_tolerance = FaultToleranceManager()

        # Seguridad Fernet
        self.security_manager = ServerSecurityManager()
        self._setup_client_keys()

        # Estado del entrenamiento
        self.current_round = 0
        self.model_version = 0
        self.global_weights = weights_to_dict(self.global_model)
        self.training_history: List[Dict[str, Any]] = []

        # Estructuras para sincronización de rondas
        self.round_lock = threading.Lock()
        self.round_updates: Dict[str, Dict[str, Any]] = {}
        self.round_condition = threading.Condition(self.round_lock)

        # Restaurar checkpoint si se solicita y existe
        if restore_checkpoint:
            state = self.fault_tolerance.restore_latest_checkpoint()
            if state:
                self.current_round = state.get("round", 0)
                self.model_version = state.get("model_version", 0)
                self.global_weights = state.get("global_weights", self.global_weights)
                set_model_weights(self.global_model, self.global_weights)
                logger.info(f"Servidor restaurado en ronda {self.current_round}.")

        # Módulo de comunicación de red TCP
        self.comm = ServerCommunication(
            host=self.host,
            port=self.port,
            security_manager=self.security_manager,
            use_encryption=self.use_encryption,
            timeout=self.round_timeout
        )

    def _setup_client_keys(self):
        """Carga o asocia las claves Fernet de los clientes."""
        client_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "client")
        for cid in ["client_1", "client_2"]:
            key_file = os.path.join(client_dir, f".{cid}.key")
            if os.path.exists(key_file):
                with open(key_file, "rb") as f:
                    self.security_manager.register_client_key(cid, f.read().strip())
            else:
                # Generar o cargar vía ClientSecurityManager
                mgr = ClientSecurityManager(cid)
                self.security_manager.register_client_key(cid, mgr.get_key())

    def handle_request(self, req: Dict[str, Any], client_addr: tuple) -> Dict[str, Any]:
        """Despacha y atiende solicitudes entrantes de clientes."""
        service = req.get("service")
        client_id = req.get("client_id", "unknown")
        round_requested = req.get("round", 0)
        message_id = req.get("message_id")

        if service == "ping":
            return {"status": "success", "round": self.current_round, "message": "pong"}

        elif service == "get_global_model":
            with self.round_lock:
                return {
                    "status": "success",
                    "round": self.current_round,
                    "model_version": self.model_version,
                    "message": "Global model delivered",
                    "client_id": client_id,
                    "weights": self.global_weights
                }

        elif service == "training_report":
            # Verificar idempotencia para prevenir agregación duplicada
            if message_id and self.fault_tolerance.is_duplicate_message(message_id):
                logger.warning(f"Mensaje duplicado descartado de {client_id} (ID: {message_id})")
                return {
                    "status": "received",
                    "round": self.current_round,
                    "message": "Actualización duplicada ignorada",
                    "client_id": client_id
                }

            samples = req.get("samples", 0)
            local_loss = req.get("local_loss", 0.0)
            deltas = req.get("deltas", {})

            with self.round_condition:
                if round_requested != self.current_round:
                    logger.warning(f"Reporte de {client_id} recibido para ronda {round_requested}, pero la actual es {self.current_round}.")
                    return {
                        "status": "error",
                        "round": self.current_round,
                        "message": f"Desfase de ronda. Ronda activa: {self.current_round}"
                    }

                # Registrar actualización del cliente
                self.round_updates[client_id] = {
                    "samples": samples,
                    "loss": local_loss,
                    "deltas": deltas,
                    "timestamp": time.time()
                }
                logger.info(f"Actualización recibida de {client_id} (muestras={samples}, loss={local_loss:.4f})")
                self.fault_tolerance.log_event("UPDATE_RECEIVED", {
                    "client_id": client_id,
                    "round": self.current_round,
                    "samples": samples,
                    "loss": local_loss
                })

                # Notificar al coordinador de ronda
                self.round_condition.notify_all()

                return {
                    "status": "received",
                    "round": self.current_round,
                    "message": f"Actualización procesada para ronda {self.current_round}",
                    "client_id": client_id
                }

        return {"status": "error", "round": self.current_round, "message": f"Servicio '{service}' no implementado"}

    def run_federated_orchestration(self):
        """
        Bucle orquestador del Servidor:
        Avanza ronda por ronda esperando las actualizaciones de los clientes,
        aplica FedAvg, evalúa y guarda checkpoints.
        """
        logger.info(f"=== INICIANDO ORQUESTACIÓN FEDERADA (Total Rondas={self.total_rounds}) ===")
        
        # Evaluación inicial de referencia (Ronda 0)
        initial_eval = self.evaluator.evaluate_weights(self.global_weights, use_test_set=True)
        logger.info(f"[Ronda 0 - Modelo Inicial] Test MAE: {initial_eval['mae']:.4f} | RMSE: {initial_eval['rmse']:.4f}")
        self.training_history.append({
            "round": 0,
            "mae": initial_eval["mae"],
            "mse": initial_eval["mse"],
            "rmse": initial_eval["rmse"],
            "loss": initial_eval["loss"],
            "participating_clients": 0
        })

        while self.current_round < self.total_rounds:
            round_start_time = time.time()
            self.current_round += 1
            logger.info(f"\n--- Iniciando Ronda Federada {self.current_round} / {self.total_rounds} ---")

            with self.round_lock:
                self.round_updates.clear()

            # Esperar a que se reciban actualizaciones de los clientes
            t_wait_start = time.time()
            with self.round_condition:
                while len(self.round_updates) < self.min_clients:
                    elapsed = time.time() - t_wait_start
                    if elapsed >= self.round_timeout:
                        break
                    remaining = self.round_timeout - elapsed
                    self.round_condition.wait(timeout=remaining)

            with self.round_lock:
                received_clients = list(self.round_updates.keys())
                num_received = len(received_clients)
                logger.info(f"Ronda {self.current_round}: Actualizaciones recibidas ({num_received}/{self.min_clients}) de {received_clients}")

                if num_received == 0:
                    logger.error(f"Fallo de ronda {self.current_round}: Ningún cliente envió actualización tras {self.round_timeout}s.")
                    self.fault_tolerance.log_failure("TIMEOUT_ALL_CLIENTS", "ALL", f"Timeout en ronda {self.current_round}")
                    continue

                if num_received < self.min_clients:
                    missing = ["client_1", "client_2"]
                    for c in received_clients:
                        if c in missing: missing.remove(c)
                    logger.warning(f"Tolerancia a fallos activada: Cliente(s) caído(s) {missing}. Continuando agregación parcial con {received_clients}.")
                    self.fault_tolerance.log_failure("PARTIAL_CLIENT_FAILURE", str(missing), f"Agregación con {received_clients}")

                # 1. Agregación FedAvg
                client_updates_list = [
                    (cid, data["samples"], data["deltas"])
                    for cid, data in self.round_updates.items()
                    if data["deltas"]
                ]

                if client_updates_list:
                    new_weights, _ = FedAvgAggregator.aggregate_deltas(
                        self.global_weights,
                        client_updates_list
                    )
                    self.global_weights = new_weights
                    self.model_version += 1
                    set_model_weights(self.global_model, self.global_weights)

                # 2. Evaluación global sobre el conjunto de test
                eval_metrics = self.evaluator.evaluate_weights(self.global_weights, use_test_set=True)
                round_duration = time.time() - round_start_time

                logger.info(f"[Ronda {self.current_round} COMPLETADA] MAE: {eval_metrics['mae']:.4f} | RMSE: {eval_metrics['rmse']:.4f} | Duración: {round_duration:.2f}s")

                history_entry = {
                    "round": self.current_round,
                    "mae": eval_metrics["mae"],
                    "mse": eval_metrics["mse"],
                    "rmse": eval_metrics["rmse"],
                    "loss": eval_metrics["loss"],
                    "participating_clients": num_received,
                    "clients": received_clients,
                    "duration_sec": round_duration
                }
                self.training_history.append(history_entry)

                # 3. Guardar checkpoint tolerante a fallos
                self.fault_tolerance.save_checkpoint(
                    current_round=self.current_round,
                    model_version=self.model_version,
                    global_weights=self.global_weights,
                    round_metrics=eval_metrics
                )

        logger.info("\n=== ENTRENAMIENTO FEDERADO FINALIZADO EXITOSAMENTE ===")
        return self.training_history

    def start(self):
        """Inicia el servidor TCP y la orquestación federada."""
        self.comm.start(self.handle_request)
        try:
            return self.run_federated_orchestration()
        finally:
            self.comm.stop()

def main():
    parser = argparse.ArgumentParser(description="Servidor Coordinador Federado - AIR_QUALITY_DISTRIBUTED")
    parser.add_argument("--host", default="0.0.0.0", help="Dirección IP de escucha (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5000, help="Puerto TCP (default: 5000)")
    parser.add_argument("--rounds", type=int, default=5, help="Número de rondas federadas (default: 5)")
    parser.add_argument("--min-clients", type=int, default=2, help="Mínimo de clientes por ronda (default: 2)")
    parser.add_argument("--encryption", action="store_true", help="Habilitar cifrado Fernet")
    parser.add_argument("--format", default="json", choices=["json", "xml"], help="Formato de serialización preferido")
    parser.add_argument("--timeout", type=float, default=30.0, help="Timeout de ronda en segundos")
    parser.add_argument("--restore", action="store_true", help="Restaurar estado desde el último checkpoint")
    args = parser.parse_args()

    server = FederatedServer(
        host=args.host,
        port=args.port,
        total_rounds=args.rounds,
        min_clients=args.min_clients,
        use_encryption=args.encryption,
        preferred_format=args.format,
        round_timeout=args.timeout,
        restore_checkpoint=args.restore
    )
    server.start()

if __name__ == "__main__":
    main()
