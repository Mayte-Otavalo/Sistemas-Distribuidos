"""
Experimento E01: Modelo Centralizado de Referencia (Baseline).
Entrena la red neuronal MLP utilizando el conjunto consolidado de entrenamiento
y evalúa sobre el mismo conjunto de test global no visto.
"""

import os
import sys
import time
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np

# Añadir raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.global_model import AirQualityMLP
from client.data_loader import AirQualityDataset, get_evaluation_dataloader
from torch.utils.data import DataLoader

def run_centralized_experiment(
    c1_path="client/local_data/client_1/iid_train.csv",
    c2_path="client/local_data/client_2/iid_train.csv",
    test_path="server/global_test.csv",
    val_path="server/global_val.csv",
    results_dir="results/centralized",
    epochs=15,
    lr=0.005,
    batch_size=32
):
    print("=" * 60)
    print("EXPERIMENTO E01: ENTRENAMIENTO CENTRALIZADO (BASELINE)")
    print("=" * 60)

    os.makedirs(results_dir, exist_ok=True)

    # 1. Consolidar datos de entrenamiento centralizados
    df1 = pd.read_csv(c1_path)
    df2 = pd.read_csv(c2_path)
    train_df = pd.concat([df1, df2], ignore_index=True)

    print(f"Total muestras de entrenamiento centralizado: {len(train_df)}")

    train_dataset = AirQualityDataset(train_df)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = get_evaluation_dataloader(test_path, batch_size=128)

    # 2. Inicializar modelo
    torch.manual_seed(42)
    model = AirQualityMLP()
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)

    # 3. Ciclo de entrenamiento
    start_time = time.time()
    history = []

    for epoch in range(1, epochs + 1):
        model.train()
        epoch_loss = 0.0
        for X, y in train_loader:
            optimizer.zero_grad()
            preds = model(X)
            loss = criterion(preds, y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * len(X)
        
        train_loss = epoch_loss / len(train_dataset)

        # Evaluar sobre test
        model.eval()
        test_loss = 0.0
        preds_list = []
        targets_list = []
        with torch.no_grad():
            for X_t, y_t in test_loader:
                p = model(X_t)
                l = criterion(p, y_t)
                test_loss += l.item() * len(X_t)
                preds_list.extend(p.view(-1).cpu().numpy())
                targets_list.extend(y_t.view(-1).cpu().numpy())

        test_loss /= len(preds_list)
        preds_arr = np.array(preds_list)
        targets_arr = np.array(targets_list)
        mae = float(np.mean(np.abs(preds_arr - targets_arr)))
        mse = float(np.mean((preds_arr - targets_arr) ** 2))
        rmse = float(np.sqrt(mse))

        history.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "test_loss": test_loss,
            "mae": mae,
            "mse": mse,
            "rmse": rmse
        })
        if epoch % 3 == 0 or epoch == epochs:
            print(f"Época {epoch:2d}/{epochs:2d} | Train Loss: {train_loss:.4f} | Test MAE: {mae:.4f} | RMSE: {rmse:.4f}")

    total_training_time = time.time() - start_time
    print(f"Entrenamiento centralizado completado en {total_training_time:.2f} segundos.")

    # Guardar métricas y predicciones
    history_df = pd.DataFrame(history)
    history_df["total_training_time_sec"] = total_training_time
    history_df.to_csv(os.path.join(results_dir, "metrics.csv"), index=False)

    preds_df = pd.DataFrame({
        "actual": targets_arr,
        "predicted": preds_arr
    })
    preds_df.to_csv(os.path.join(results_dir, "predictions.csv"), index=False)
    print(f"Resultados guardados en {results_dir}/metrics.csv y predictions.csv")
    return history_df

if __name__ == "__main__":
    run_centralized_experiment()
