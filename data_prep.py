"""
Script de preparación y análisis de datos para el proyecto AIR_QUALITY_DISTRIBUTED.
Fase 1: Limpieza, tratamiento de -200, partición IID y Non-IID, y normalización sin data leakage.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def prepare_air_quality_data(
    raw_path="data_raw/AirQualityUCI.csv",
    output_dir_client1="client/local_data/client_1",
    output_dir_client2="client/local_data/client_2",
    output_dir_server="server",
    results_dir="results/data_analysis",
    figures_dir="results/figures"
):
    print("=" * 60)
    print("FASE 1: ANÁLISIS Y PREPARACIÓN DE DATOS (Air Quality)")
    print("=" * 60)

    # 1. Cargar archivo crudo
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Archivo crudo no encontrado: {raw_path}")

    df = pd.read_csv(raw_path, sep=';', decimal=',', encoding='latin1')
    
    # Eliminar columnas sin nombre residuales producidas por delimitadores finales ';;'
    unnamed_cols = [c for c in df.columns if 'Unnamed' in c or c.strip() == '']
    if unnamed_cols:
        df = df.drop(columns=unnamed_cols)

    # Eliminar filas totalmente vacías
    df = df.dropna(how='all')

    print(f"[1] Dataset cargado: {df.shape[0]} filas, {df.shape[1]} columnas.")

    # 2. Formatear Fecha y Hora
    # En el dataset, Date es DD/MM/YYYY y Time es HH.MM.SS
    df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'].str.replace('.', ':', regex=False), format='%d/%m/%Y %H:%M:%S', errors='coerce')
    df = df.sort_values('Datetime').reset_index(drop=True)

    # 3. Tratamiento de valores faltantes (-200)
    features_target = [
        'CO(GT)', 'PT08.S1(CO)', 'NMHC(GT)', 'C6H6(GT)', 'PT08.S2(NMHC)',
        'NOx(GT)', 'PT08.S3(NOx)', 'NO2(GT)', 'PT08.S4(NO2)', 'PT08.S5(O3)',
        'T', 'RH', 'AH'
    ]

    # Reemplazar -200 por NaN
    for col in features_target:
        if col in df.columns:
            df[col] = df[col].astype(float)
            df.loc[df[col] <= -200, col] = np.nan

    # Diagnóstico de faltantes
    missing_summary = df[features_target].isnull().sum()
    missing_pct = (missing_summary / len(df)) * 100
    summary_df = pd.DataFrame({
        'Feature': features_target,
        'Missing_Count': missing_summary.values,
        'Missing_Pct': missing_pct.values,
        'Mean': df[features_target].mean().values,
        'Std': df[features_target].std().values,
        'Min': df[features_target].min().values,
        'Max': df[features_target].max().values
    })
    
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(figures_dir, exist_ok=True)
    summary_df.to_csv(os.path.join(results_dir, "dataset_summary.csv"), index=False)
    print("\n[2] Resumen de calidad y valores faltantes guardado en results/data_analysis/dataset_summary.csv")

    # Observación: NMHC(GT) tiene >90% de valores faltantes en este dataset estándar.
    # Si una variable tiene casi todos faltantes, se puede imputar por mediana o descartar.
    # Para conservar todas las columnas de la guía, imputamos linealmente en el tiempo o con mediana.
    for col in features_target:
        # Interpolación lineal temporal para gaps pequeños, luego bfill y ffill
        df[col] = df[col].interpolate(method='linear', limit_direction='both')
        if df[col].isnull().sum() > 0:
            df[col] = df[col].fillna(df[col].median())

    # Asegurar que no queden NaNs
    df = df.dropna(subset=features_target).reset_index(drop=True)
    print(f"[3] Filas tras imputación e interpolación: {len(df)}")

    # 4. División Train (70%), Val (15%), Test (15%) temporal
    n_total = len(df)
    n_train = int(n_total * 0.70)
    n_val = int(n_total * 0.15)
    n_test = n_total - n_train - n_val

    train_df = df.iloc[:n_train].copy().reset_index(drop=True)
    val_df = df.iloc[n_train:n_train+n_val].copy().reset_index(drop=True)
    test_df = df.iloc[n_train+n_val:].copy().reset_index(drop=True)

    print(f"[4] Partición temporal global: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")

    # 5. Normalización StandardScaler (ajustada SÓLO en train_df para evitar data leakage)
    target_col = 'CO(GT)'
    input_cols = [c for c in features_target if c != target_col]

    means = train_df[input_cols].mean()
    stds = train_df[input_cols].std().replace(0, 1.0)

    target_mean = train_df[target_col].mean()
    target_std = train_df[target_col].std() if train_df[target_col].std() > 0 else 1.0

    # Guardar parámetros de escala para normalizar/desnormalizar consistentemente
    scaler_params = pd.DataFrame({
        'feature': input_cols + [target_col],
        'mean': list(means) + [target_mean],
        'std': list(stds) + [target_std]
    })
    scaler_params.to_csv(os.path.join(results_dir, "scaler_params.csv"), index=False)

    def normalize(data_subset):
        normalized = data_subset.copy()
        for col in input_cols:
            normalized[col] = (normalized[col] - means[col]) / stds[col]
        normalized[target_col] = (normalized[target_col] - target_mean) / target_std
        return normalized

    train_norm = normalize(train_df)
    val_norm = normalize(val_df)
    test_norm = normalize(test_df)

    # 6. Partición IID para clientes (50% Client 1, 50% Client 2 aleatorio equilibrado)
    np.random.seed(42)
    indices = np.random.permutation(len(train_norm))
    half = len(indices) // 2
    c1_iid_idx = indices[:half]
    c2_iid_idx = indices[half:]

    client1_iid = train_norm.iloc[c1_iid_idx].copy().reset_index(drop=True)
    client2_iid = train_norm.iloc[c2_iid_idx].copy().reset_index(drop=True)

    # 7. Partición Non-IID para clientes (División temporal: primer periodo Client 1, segundo Client 2)
    client1_non_iid = train_norm.iloc[:half].copy().reset_index(drop=True)
    client2_non_iid = train_norm.iloc[half:].copy().reset_index(drop=True)

    # 8. Guardar datasets locales por cliente (sin acceso mutuo a archivos privados)
    os.makedirs(output_dir_client1, exist_ok=True)
    os.makedirs(output_dir_client2, exist_ok=True)
    os.makedirs(output_dir_server, exist_ok=True)

    save_cols = ['Datetime'] + features_target

    client1_iid[save_cols].to_csv(os.path.join(output_dir_client1, "iid_train.csv"), index=False)
    client2_iid[save_cols].to_csv(os.path.join(output_dir_client2, "iid_train.csv"), index=False)

    client1_non_iid[save_cols].to_csv(os.path.join(output_dir_client1, "non_iid_train.csv"), index=False)
    client2_non_iid[save_cols].to_csv(os.path.join(output_dir_client2, "non_iid_train.csv"), index=False)

    val_norm[save_cols].to_csv(os.path.join(output_dir_server, "global_val.csv"), index=False)
    test_norm[save_cols].to_csv(os.path.join(output_dir_server, "global_test.csv"), index=False)

    # Guardar copias locales de validación para monitorización local de cada cliente
    client1_iid.sample(frac=0.15, random_state=42)[save_cols].to_csv(os.path.join(output_dir_client1, "local_val.csv"), index=False)
    client2_iid.sample(frac=0.15, random_state=42)[save_cols].to_csv(os.path.join(output_dir_client2, "local_val.csv"), index=False)

    print(f"[5] Datos guardados en client_1, client_2 y server:")
    print(f"    - Client 1 IID: {len(client1_iid)} filas | Non-IID: {len(client1_non_iid)} filas")
    print(f"    - Client 2 IID: {len(client2_iid)} filas | Non-IID: {len(client2_non_iid)} filas")
    print(f"    - Server Val: {len(val_norm)} filas | Server Test: {len(test_norm)} filas")

    # 9. Estadísticas comparativas IID y Non-IID
    iid_stats = pd.DataFrame({
        'Client 1 Mean CO': [client1_iid['CO(GT)'].mean()],
        'Client 1 Std CO': [client1_iid['CO(GT)'].std()],
        'Client 2 Mean CO': [client2_iid['CO(GT)'].mean()],
        'Client 2 Std CO': [client2_iid['CO(GT)'].std()],
        'Samples C1': [len(client1_iid)],
        'Samples C2': [len(client2_iid)]
    })
    iid_stats.to_csv(os.path.join(results_dir, "iid_distribution.csv"), index=False)

    non_iid_stats = pd.DataFrame({
        'Client 1 Mean CO': [client1_non_iid['CO(GT)'].mean()],
        'Client 1 Std CO': [client1_non_iid['CO(GT)'].std()],
        'Client 2 Mean CO': [client2_non_iid['CO(GT)'].mean()],
        'Client 2 Std CO': [client2_non_iid['CO(GT)'].std()],
        'Samples C1': [len(client1_non_iid)],
        'Samples C2': [len(client2_non_iid)]
    })
    non_iid_stats.to_csv(os.path.join(results_dir, "non_iid_distribution.csv"), index=False)

    # 10. Generar Gráficas comparativas de distribución
    plt.figure(figsize=(12, 5))

    # Gráfica IID
    plt.subplot(1, 2, 1)
    sns.kdeplot(client1_iid['CO(GT)'], label='Cliente 1 (IID)', color='navy', fill=True, alpha=0.3)
    sns.kdeplot(client2_iid['CO(GT)'], label='Cliente 2 (IID)', color='crimson', fill=True, alpha=0.3)
    plt.title('Distribución IID de CO(GT) Normalizada')
    plt.xlabel('CO(GT) (Escalado)')
    plt.ylabel('Densidad')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Gráfica Non-IID
    plt.subplot(1, 2, 2)
    sns.kdeplot(client1_non_iid['CO(GT)'], label='Cliente 1 (Periodo 1)', color='navy', fill=True, alpha=0.3)
    sns.kdeplot(client2_non_iid['CO(GT)'], label='Cliente 2 (Periodo 2)', color='crimson', fill=True, alpha=0.3)
    plt.title('Distribución Non-IID de CO(GT) (Heterogeneidad Temporal)')
    plt.xlabel('CO(GT) (Escalado)')
    plt.ylabel('Densidad')
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    fig_path = os.path.join(figures_dir, "iid_vs_non_iid.png")
    plt.savefig(fig_path, dpi=300)
    plt.close()
    print(f"[6] Gráfica comparativa IID vs Non-IID guardada en: {fig_path}")
    print("=" * 60)
    print("FASE 1 COMPLETADA EXITOSAMENTE")
    print("=" * 60)

if __name__ == "__main__":
    prepare_air_quality_data()
