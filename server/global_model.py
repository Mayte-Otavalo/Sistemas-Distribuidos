"""
Definición de la arquitectura de la red neuronal MLP y gestión de parámetros
para el modelo global y local (AIR_QUALITY_DISTRIBUTED).
"""

import torch
import torch.nn as nn
from typing import Dict, Any, List

class AirQualityMLP(nn.Module):
    """
    Red Neuronal Perceptrón Multicapa (MLP) para regresión de calidad del aire (CO(GT)).
    Arquitectura homogénea entre todos los nodos: Servidor, PC Cliente y Raspberry Pi.
    """
    def __init__(self, input_dim: int = 12, hidden_dim1: int = 64, hidden_dim2: int = 32):
        super(AirQualityMLP, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim1),
            nn.ReLU(),
            nn.Linear(hidden_dim1, hidden_dim2),
            nn.ReLU(),
            nn.Linear(hidden_dim2, 1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)

def weights_to_dict(model: nn.Module) -> Dict[str, List[float]]:
    """Serializa los tensores de pesos del modelo a listas de números flotantes (para JSON/XML)."""
    weights = {}
    for name, param in model.state_dict().items():
        weights[name] = param.detach().cpu().numpy().tolist()
    return weights

def dict_to_weights(weights_dict: Dict[str, Any]) -> Dict[str, torch.Tensor]:
    """Convierte un diccionario de listas a tensores de PyTorch para el state_dict."""
    state_dict = {}
    for name, val in weights_dict.items():
        state_dict[name] = torch.tensor(val, dtype=torch.float32)
    return state_dict

def set_model_weights(model: nn.Module, weights_dict: Dict[str, Any]):
    """Carga pesos en el modelo a partir de un diccionario."""
    state_dict = dict_to_weights(weights_dict)
    model.load_state_dict(state_dict)

def compute_deltas(local_model: nn.Module, global_weights_dict: Dict[str, Any]) -> Dict[str, List[float]]:
    """
    Calcula los deltas de entrenamiento local:
    Delta = W_local - W_global
    """
    local_sd = local_model.state_dict()
    global_sd = dict_to_weights(global_weights_dict)
    deltas = {}
    for k in local_sd.keys():
        diff = local_sd[k] - global_sd[k]
        deltas[k] = diff.detach().cpu().numpy().tolist()
    return deltas
