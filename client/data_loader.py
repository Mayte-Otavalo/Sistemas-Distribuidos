"""
Módulo de carga y preparación de datos para los clientes federados.
Asegura aislamiento de datos locales para cada cliente.
"""

import os
import torch
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np

TARGET_COLUMN = 'CO(GT)'
FEATURE_COLUMNS = [
    'PT08.S1(CO)', 'NMHC(GT)', 'C6H6(GT)', 'PT08.S2(NMHC)',
    'NOx(GT)', 'PT08.S3(NOx)', 'NO2(GT)', 'PT08.S4(NO2)', 'PT08.S5(O3)',
    'T', 'RH', 'AH'
]

class AirQualityDataset(Dataset):
    def __init__(self, df: pd.DataFrame):
        self.X = torch.tensor(df[FEATURE_COLUMNS].values, dtype=torch.float32)
        self.y = torch.tensor(df[TARGET_COLUMN].values, dtype=torch.float32).unsqueeze(1)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

def get_client_dataloader(
    client_id: str,
    distribution_type: str = "iid",
    batch_size: int = 32,
    shuffle: bool = True,
    base_dir: str = None
) -> tuple[DataLoader, int]:
    """
    Carga el conjunto de entrenamiento local para un cliente específico.
    Garantiza que ningún cliente acceda a los datos privados del otro.
    """
    if base_dir is None:
        # Ruta por defecto relativa al módulo o al workspace
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        client_dir = os.path.join(cur_dir, "local_data", client_id)
    else:
        client_dir = os.path.join(base_dir, client_id)

    filename = f"{distribution_type}_train.csv"
    filepath = os.path.join(client_dir, filename)

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No se encontró el dataset para {client_id} en {filepath}")

    df = pd.read_csv(filepath)
    dataset = AirQualityDataset(df)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=shuffle)
    num_samples = len(df)
    return loader, num_samples

def get_evaluation_dataloader(filepath: str, batch_size: int = 64) -> DataLoader:
    """
    Carga un conjunto de evaluación (utilizado por el servidor global o validación local).
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Archivo de evaluación no encontrado: {filepath}")
    df = pd.read_csv(filepath)
    dataset = AirQualityDataset(df)
    return DataLoader(dataset, batch_size=batch_size, shuffle=False)
