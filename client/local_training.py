"""
Módulo de entrenamiento local y cálculo de deltas para el Cliente Federado (AIR_QUALITY_DISTRIBUTED).
"""

import copy
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Dict, Any, Tuple
from client.data_loader import get_client_dataloader
from server.global_model import AirQualityMLP, set_model_weights, compute_deltas

class LocalTrainer:
    def __init__(
        self,
        client_id: str,
        distribution_type: str = "iid",
        learning_rate: float = 0.005,
        local_epochs: int = 3,
        batch_size: int = 32
    ):
        self.client_id = client_id
        self.distribution_type = distribution_type
        self.lr = learning_rate
        self.epochs = local_epochs
        self.batch_size = batch_size
        self.criterion = nn.MSELoss()

    def train_round(
        self,
        global_weights_dict: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], int, float]:
        """
        Ejecuta el ciclo de entrenamiento local de una ronda federada:
        1. Inicializa modelo y carga pesos globales.
        2. Carga datos locales del cliente.
        3. Entrena durante E épocas locales.
        4. Calcula los deltas: Delta = W_local - W_global.
        5. Retorna (deltas_dict, num_samples, final_loss).
        """
        # Cargar datos locales de entrenamiento
        dataloader, num_samples = get_client_dataloader(
            self.client_id,
            distribution_type=self.distribution_type,
            batch_size=self.batch_size,
            shuffle=True
        )

        model = AirQualityMLP()
        set_model_weights(model, global_weights_dict)
        model.train()

        optimizer = optim.Adam(model.parameters(), lr=self.lr)

        total_loss = 0.0
        batches_count = 0

        for epoch in range(self.epochs):
            epoch_loss = 0.0
            for X, y in dataloader:
                optimizer.zero_grad()
                preds = model(X)
                loss = self.criterion(preds, y)
                loss.backward()
                optimizer.step()

                epoch_loss += loss.item()
                batches_count += 1
            total_loss = epoch_loss / len(dataloader)

        # Calcular deltas
        deltas = compute_deltas(model, global_weights_dict)

        return deltas, num_samples, total_loss
