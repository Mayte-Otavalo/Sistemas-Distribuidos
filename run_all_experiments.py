"""
Script Orquestador Maestro de la Matriz de Experimentos (E01 - E08)
para el proyecto AIR_QUALITY_DISTRIBUTED.
Ejecuta todos los experimentos de forma reproducible y genera todas las métricas y gráficos.
"""

import sys
import time

from experiments.centralized_baseline import run_centralized_experiment
from experiments.iid.run_iid import run_iid_experiment
from experiments.non_iid.run_non_iid import run_non_iid_experiment
from experiments.json_vs_xml.run_benchmark import run_json_vs_xml_experiment
from experiments.encryption_benchmark import run_encryption_experiment
from experiments.fault_tolerance.run_fault_tests import run_fault_tolerance_experiments
from experiments.generate_plots import plot_json_vs_xml, plot_centralized_vs_federated, plot_fault_recovery

def main():
    total_start = time.time()
    print("=" * 80)
    print("EJECUTANDO LA MATRIZ COMPLETA DE EXPERIMENTACIÓN (E01 - E08)")
    print("AIR_QUALITY_DISTRIBUTED - SISTEMAS DISTRIBUIDOS")
    print("=" * 80)

    # E01: Centralizado
    print("\n>>> PASO 1/7: Experimento E01 (Entrenamiento Centralizado) <<<")
    run_centralized_experiment(epochs=10)

    # E02: Federado IID
    print("\n>>> PASO 2/7: Experimento E02 (Aprendizaje Federado IID) <<<")
    run_iid_experiment(rounds=5, port=5601, epochs=2)

    # E03: Federado Non-IID
    print("\n>>> PASO 3/7: Experimento E03 (Aprendizaje Federado Non-IID) <<<")
    run_non_iid_experiment(rounds=5, port=5602, epochs=2)

    # E04: JSON vs XML
    print("\n>>> PASO 4/7: Experimento E04 (JSON vs XML Benchmarking) <<<")
    run_json_vs_xml_experiment(repetitions=30)

    # E05: Cifrado Fernet vs Plano
    print("\n>>> PASO 5/7: Experimento E05 (Impacto de Cifrado Fernet) <<<")
    run_encryption_experiment(repetitions=30, port_plain=5603, port_enc=5604)

    # E06, E07, E08: Tolerancia a Fallos
    print("\n>>> PASO 6/7: Experimentos E06, E07, E08 (Tolerancia a Fallos) <<<")
    run_fault_tolerance_experiments(port=5605)

    # Generación de gráficos y figuras
    print("\n>>> PASO 7/7: Generación de Gráficos y Visualizaciones Comparativas <<<")
    plot_json_vs_xml()
    plot_centralized_vs_federated()
    plot_fault_recovery()

    total_time = time.time() - total_start
    print("\n" + "=" * 80)
    print(f"MATRIZ EXPERIMENTAL COMPLETADA EXITOSAMENTE EN {total_time:.2f} SEGUNDOS.")
    print("Todos los resultados CSV y figuras PNG están disponibles en la carpeta results/.")
    print("=" * 80)

if __name__ == "__main__":
    main()
