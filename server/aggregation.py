"""
Implementación del algoritmo Federated Averaging (FedAvg) basado en Deltas de pesos
para el Servidor Coordinador (AIR_QUALITY_DISTRIBUTED).
"""

import torch
import torch.nn as nn
from typing import List, Dict, Any, Tuple
from server.global_model import dict_to_weights, weights_to_dict

class FedAvgAggregator:
    @staticmethod
    def aggregate_deltas(
        current_global_weights: Dict[str, Any],
        client_updates: List[Tuple[str, int, Dict[str, Any]]]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Calcula la agregación federada de deltas:
        Delta_g = sum_k ( (n_k / N_total) * Delta_k )
        W_nuevo = W_anterior + Delta_g

        client_updates: lista de tuplas (client_id, num_samples, deltas_dict)
        Retorna (nuevo_global_weights, aggregated_deltas)
        """
        if not client_updates:
            return current_global_weights, {}

        total_samples = sum(num_samples for _, num_samples, _ in client_updates)
        if total_samples <= 0:
            raise ValueError("El número total de muestras recibidas debe ser mayor a cero.")

        curr_sd = dict_to_weights(current_global_weights)
        first_deltas = dict_to_weights(client_updates[0][2])
        
        # Inicializar delta global con ceros
        aggregated_deltas = {k: torch.zeros_like(v) for k, v in first_deltas.items()}

        for cid, n_k, deltas_dict in client_updates:
            weight = float(n_k) / float(total_samples)
            d_sd = dict_to_weights(deltas_dict)
            for k in aggregated_deltas.keys():
                if k not in d_sd:
                    raise KeyError(f"Parámetro '{k}' ausente en el reporte del cliente '{cid}'.")
                aggregated_deltas[k] += weight * d_sd[k]

        # Actualizar modelo global: W_new = W_old + Delta_g
        new_global_weights_sd = {}
        for k in curr_sd.keys():
            new_global_weights_sd[k] = curr_sd[k] + aggregated_deltas[k]

        # Convertir a diccionarios serializables
        new_global_dict = {}
        for k, v in new_global_weights_sd.items():
            new_global_dict[k] = v.detach().cpu().numpy().tolist()

        agg_deltas_dict = {}
        for k, v in aggregated_deltas.items():
            agg_deltas_dict[k] = v.detach().cpu().numpy().tolist()

        return new_global_dict, agg_deltas_dict
