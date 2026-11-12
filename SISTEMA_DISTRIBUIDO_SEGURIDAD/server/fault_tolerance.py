"""
Módulo de Tolerancia a Fallos, Persistencia y Recuperación para el Servidor Coordinador (AIR_QUALITY_DISTRIBUTED).
Gestiona:
- Checkpoints atómicos de estado del modelo y ronda.
- Detección de mensajes duplicados / Idempotencia.
- Bitácora estructurada de eventos y fallos.
- Restauración ante fallos del servidor y desconexiones de clientes.
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional, Set, Tuple

logger = logging.getLogger("FaultTolerance")

class FaultToleranceManager:
    def __init__(
        self,
        checkpoint_dir: str = "server/checkpoints",
        logs_dir: str = "server/logs",
        client_timeout_sec: float = 25.0
    ):
        self.checkpoint_dir = checkpoint_dir
        self.logs_dir = logs_dir
        self.client_timeout_sec = client_timeout_sec
        
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

        self.latest_checkpoint_file = os.path.join(self.checkpoint_dir, "latest_state.json")
        self.failure_log_file = os.path.join(self.logs_dir, "failures.log")
        self.event_log_file = os.path.join(self.logs_dir, "events.log")

        # Registro de IDs de mensajes procesados para prevenir duplicación (Idempotencia)
        self.processed_message_ids: Set[str] = set()

        # Métricas de fallos
        self.metrics = {
            "failure_events_detected": 0,
            "recoveries_completed": 0,
            "duplicate_messages_discarded": 0,
            "client_timeouts": 0,
            "checkpoint_restores": 0
        }

    def log_event(self, event_type: str, details: Dict[str, Any]):
        """Registra un evento operativo en el log."""
        entry = {
            "timestamp": time.time(),
            "iso_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event_type": event_type,
            "details": details
        }
        try:
            with open(self.event_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Error escribiendo en event_log: {e}")

    def log_failure(self, failure_type: str, node: str, description: str, duration_sec: float = 0.0):
        """Registra un evento de fallo o desconexión."""
        self.metrics["failure_events_detected"] += 1
        entry = {
            "timestamp": time.time(),
            "iso_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "failure_type": failure_type,
            "node": node,
            "description": description,
            "duration_sec": duration_sec
        }
        try:
            with open(self.failure_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Error escribiendo en failure_log: {e}")

    def is_duplicate_message(self, message_id: Optional[str]) -> bool:
        """Verifica si un identificador único de actualización ya fue procesado."""
        if not message_id:
            return False
        if message_id in self.processed_message_ids:
            self.metrics["duplicate_messages_discarded"] += 1
            self.log_event("DUPLICATE_MESSAGE_IGNORED", {"message_id": message_id})
            return True
        self.processed_message_ids.add(message_id)
        return False

    def save_checkpoint(
        self,
        current_round: int,
        model_version: int,
        global_weights: Dict[str, Any],
        round_metrics: Dict[str, Any]
    ):
        """
        Guarda un checkpoint del estado actual del entrenamiento federado.
        Permite que ante una caída del servidor, se recupere la última ronda válida.
        """
        state = {
            "round": current_round,
            "model_version": model_version,
            "timestamp": time.time(),
            "iso_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "global_weights": global_weights,
            "metrics": round_metrics,
            "processed_message_ids": list(self.processed_message_ids)
        }

        # Guardar checkpoint específico de la ronda
        round_path = os.path.join(self.checkpoint_dir, f"checkpoint_round_{current_round}.json")
        try:
            with open(round_path, "w", encoding="utf-8") as f:
                json.dump(state, f)
            
            # Guardar latest_state de forma atómica
            with open(self.latest_checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(state, f)

            self.log_event("CHECKPOINT_SAVED", {"round": current_round, "model_version": model_version})
            logger.info(f"Checkpoint de ronda {current_round} persistido con éxito.")
        except Exception as e:
            logger.error(f"Error persistiendo checkpoint de ronda {current_round}: {e}")

    def restore_latest_checkpoint(self) -> Optional[Dict[str, Any]]:
        """
        Restaura el último estado guardado tras un fallo o reinicio del servidor.
        Retorna el diccionario con weights, round, metrics o None si no hay checkpoints.
        """
        if not os.path.exists(self.latest_checkpoint_file):
            return None

        try:
            t0 = time.perf_counter()
            with open(self.latest_checkpoint_file, "r", encoding="utf-8") as f:
                state = json.load(f)
            t1 = time.perf_counter()

            # Restaurar IDs procesados
            if "processed_message_ids" in state:
                self.processed_message_ids = set(state["processed_message_ids"])

            self.metrics["checkpoint_restores"] += 1
            self.metrics["recoveries_completed"] += 1
            recovery_time = (t1 - t0) * 1000.0

            self.log_event("CHECKPOINT_RESTORED", {
                "round": state.get("round"),
                "recovery_time_ms": recovery_time
            })
            logger.info(f"Servidor restaurado desde checkpoint: Ronda={state.get('round')}, Versión={state.get('model_version')}")
            return state
        except Exception as e:
            logger.error(f"Error restaurando checkpoint: {e}")
            return None
