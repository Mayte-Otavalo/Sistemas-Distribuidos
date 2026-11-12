"""
Módulo de evaluación del modelo global y cálculo de métricas de regresión (AIR_QUALITY_DISTRIBUTED).
Métricas: MAE, MSE, RMSE y Loss sobre datos no vistos.
"""

import os
import torch
import torch.nn as nn
import numpy as np
from typing import Dict, Any, Tuple
from client.data_loader import get_evaluation_dataloader
from server.global_model import AirQualityMLP, set_model_weights

class ModelEvaluator:
    def __init__(self, val_path: str = "server/global_val.csv", test_path: str = "server/global_test.csv"):
        self.val_path = val_path
        self.test_path = test_path
        self.criterion = nn.MSELoss()

    def evaluate(self, model: nn.Module, dataset_path: str) -> Dict[str, float]:
        """Evalúa el modelo sobre un conjunto de datos específico."""
        if not os.path.exists(dataset_path):
            return {"loss": 0.0, "mae": 0.0, "mse": 0.0, "rmse": 0.0}

        dataloader = get_evaluation_dataloader(dataset_path, batch_size=128)
        model.eval()

        total_loss = 0.0
        all_preds = []
        all_targets = []

        with torch.no_grad():
            for X, y in dataloader:
                preds = model(X)
                loss = self.criterion(preds, y)
                total_loss += loss.item() * len(X)
                all_preds.extend(preds.view(-1).cpu().numpy())
                all_targets.extend(y.view(-1).cpu().numpy())

        num_samples = len(all_preds)
        if num_samples == 0:
            return {"loss": 0.0, "mae": 0.0, "mse": 0.0, "rmse": 0.0}

        avg_loss = total_loss / num_samples
        preds_arr = np.array(all_preds)
        targets_arr = np.array(all_targets)

        mae = float(np.mean(np.abs(preds_arr - targets_arr)))
        mse = float(np.mean((preds_arr - targets_arr) ** 2))
        rmse = float(np.sqrt(mse))

        return {
            "loss": avg_loss,
            "mae": mae,
            "mse": mse,
            "rmse": rmse
        }

    def evaluate_weights(self, weights_dict: Dict[str, Any], use_test_set: bool = True) -> Dict[str, float]:
        """Evalúa un diccionario de pesos construyendo un modelo temporal."""
        model = AirQualityMLP()
        set_model_weights(model, weights_dict)
        target_path = self.test_path if use_test_set else self.val_path
        return self.evaluate(model, target_path)
