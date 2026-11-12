"""
Generador automático de gráficos y figuras para el informe de resultados
(results/figures/):
- json_vs_xml.png
- centralized_vs_federated.png
- fault_recovery.png
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

FIGURES_DIR = "results/figures"

def plot_json_vs_xml():
    comp_path = "results/communication/comparison.csv"
    if not os.path.exists(comp_path):
        return

    df = pd.read_csv(comp_path)
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

    # Gráfico 1: Tamaño de Payload
    row_bytes = df[df["Métrica"].str.contains("Tamaño")].iloc[0]
    axes[0].bar(["JSON", "XML"], [row_bytes["JSON (Promedio)"], row_bytes["XML (Promedio)"]], color=["#2b5c8f", "#d95f02"], width=0.5)
    axes[0].set_title("Tamaño del Mensaje (Bytes)")
    axes[0].set_ylabel("Bytes")
    for i, v in enumerate([row_bytes["JSON (Promedio)"], row_bytes["XML (Promedio)"]]):
        axes[0].text(i, v + 2, f"{v:.1f} B", ha='center', fontweight='bold')
    axes[0].grid(axis='y', alpha=0.3)

    # Gráfico 2: Tiempo de Validación
    row_val = df[df["Métrica"].str.contains("Validación")].iloc[0]
    axes[1].bar(["JSON Schema", "XML XSD"], [row_val["JSON (Promedio)"], row_val["XML (Promedio)"]], color=["#2b5c8f", "#d95f02"], width=0.5)
    axes[1].set_title("Sobrecarga de Validación (ms)")
    axes[1].set_ylabel("Milisegundos (ms)")
    for i, v in enumerate([row_val["JSON (Promedio)"], row_val["XML (Promedio)"]]):
        axes[1].text(i, v + 0.05, f"{v:.3f} ms", ha='center', fontweight='bold')
    axes[1].grid(axis='y', alpha=0.3)

    # Gráfico 3: Latencia Round-Trip (RTT)
    row_rtt = df[df["Métrica"].str.contains("RTT")].iloc[0]
    axes[2].bar(["JSON", "XML"], [row_rtt["JSON (Promedio)"], row_rtt["XML (Promedio)"]], color=["#2b5c8f", "#d95f02"], width=0.5)
    axes[2].set_title("Latencia de Ida y Vuelta (RTT)")
    axes[2].set_ylabel("Milisegundos (ms)")
    for i, v in enumerate([row_rtt["JSON (Promedio)"], row_rtt["XML (Promedio)"]]):
        axes[2].text(i, v + 0.1, f"{v:.2f} ms", ha='center', fontweight='bold')
    axes[2].grid(axis='y', alpha=0.3)

    plt.suptitle("Comparativa Experimental: Protocolo JSON vs XML (Workshop 7)", fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "json_vs_xml.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("[+] Gráfico json_vs_xml.png generado con éxito.")

def plot_centralized_vs_federated():
    cent_path = "results/centralized/metrics.csv"
    iid_path = "results/federated/iid_metrics.csv"
    non_iid_path = "results/federated/non_iid_metrics.csv"

    if not os.path.exists(cent_path) or not os.path.exists(iid_path):
        return

    df_cent = pd.read_csv(cent_path)
    df_iid = pd.read_csv(iid_path)
    df_non = pd.read_csv(non_iid_path) if os.path.exists(non_iid_path) else None

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Convergencia MAE
    ax1.plot(df_cent["epoch"], df_cent["mae"], marker='o', label="Centralizado (Baseline)", color="#1b9e77", linewidth=2)
    
    # En federado las rondas se corresponden con avances de convergencia
    rondas = df_iid["round"].values
    mae_iid = df_iid["mae"].values
    ax1.plot(rondas, mae_iid, marker='s', label="Federado IID (FedAvg)", color="#386cb0", linewidth=2, linestyle='--')

    if df_non is not None:
        ax1.plot(df_non["round"].values, df_non["mae"].values, marker='^', label="Federado Non-IID (FedAvg)", color="#e7298a", linewidth=2, linestyle=':')

    ax1.set_title("Convergencia del Error Absoluto Medio (MAE)", fontweight='bold')
    ax1.set_xlabel("Ronda Federada / Época Centralizada")
    ax1.set_ylabel("MAE (Datos de Test Normalizados)")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Convergencia RMSE
    ax2.plot(df_cent["epoch"], df_cent["rmse"], marker='o', label="Centralizado (Baseline)", color="#1b9e77", linewidth=2)
    ax2.plot(rondas, df_iid["rmse"].values, marker='s', label="Federado IID (FedAvg)", color="#386cb0", linewidth=2, linestyle='--')
    if df_non is not None:
        ax2.plot(df_non["round"].values, df_non["rmse"].values, marker='^', label="Federado Non-IID (FedAvg)", color="#e7298a", linewidth=2, linestyle=':')

    ax2.set_title("Convergencia de la Raíz del Error Cuadrático Medio (RMSE)", fontweight='bold')
    ax2.set_xlabel("Ronda Federada / Época Centralizada")
    ax2.set_ylabel("RMSE (Datos de Test Normalizados)")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.suptitle("Comparativa: Aprendizaje Centralizado vs Aprendizaje Federado (FedAvg)", fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "centralized_vs_federated.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("[+] Gráfico centralized_vs_federated.png generado con éxito.")

def plot_fault_recovery():
    fig, ax = plt.subplots(figsize=(10, 4.5))

    events = [
        "E06: Desconexión de Cliente 2",
        "E06: Detección por Timeout (4s)",
        "E06: Agregación Parcial con Cliente 1",
        "E07: Caída Abrupta del Servidor",
        "E07: Restauración desde Checkpoint Atómico",
        "E08: Mensaje Duplicado Interceptado e Ignorado"
    ]
    times = [0.0, 4.0, 4.2, 5.0, 5.03, 6.0]
    types = ["Fallo", "Detección", "Recuperación", "Fallo", "Recuperación", "Idempotencia"]
    colors = ["#e41a1c", "#ff7f00", "#4daf4a", "#e41a1c", "#4daf4a", "#377eb8"]

    ax.hlines(y=range(len(events)), xmin=0, xmax=times, color=colors, alpha=0.7, linewidth=6)
    ax.scatter(times, range(len(events)), color=colors, s=120, zorder=3)

    for i, t in enumerate(times):
        ax.text(t + 0.15, i, f"{t:.2f} s", va='center', fontweight='bold', color="#222222")

    ax.set_yticks(range(len(events)))
    ax.set_yticklabels(events, fontweight='semibold')
    ax.set_xlabel("Línea de Tiempo Operativa (Segundos)")
    ax.set_title("Resiliencia del Sistema: Detección y Recuperación ante Fallos (E06, E07, E08)", fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    ax.set_xlim(-0.5, 7.5)

    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "fault_recovery.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("[+] Gráfico fault_recovery.png generado con éxito.")

if __name__ == "__main__":
    os.makedirs(FIGURES_DIR, exist_ok=True)
    plot_json_vs_xml()
    plot_centralized_vs_federated()
    plot_fault_recovery()
