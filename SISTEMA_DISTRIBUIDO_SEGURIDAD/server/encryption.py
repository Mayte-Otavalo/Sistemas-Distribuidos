"""
Módulo de seguridad y cifrado Fernet para el Servidor Coordinador.
Mantiene claves simétricas independientes para cada cliente.
"""

import os
from typing import Dict, Optional
from cryptography.fernet import Fernet, InvalidToken

class ServerSecurityManager:
    def __init__(self, key_map: Optional[Dict[str, bytes]] = None, keys_dir: Optional[str] = None):
        self.ciphers: Dict[str, Fernet] = {}
        self.keys: Dict[str, bytes] = {}
        
        if key_map:
            for cid, k in key_map.items():
                self.register_client_key(cid, k)
        
        if keys_dir and os.path.exists(keys_dir):
            for fname in os.listdir(keys_dir):
                if fname.endswith(".key"):
                    cid = fname.replace(".key", "").replace(".", "")
                    with open(os.path.join(keys_dir, fname), "rb") as f:
                        self.register_client_key(cid, f.read().strip())

    def register_client_key(self, client_id: str, key: bytes):
        """Registra o actualiza la clave Fernet de un cliente específico."""
        if isinstance(key, str):
            key = key.encode('utf-8')
        self.keys[client_id] = key
        self.ciphers[client_id] = Fernet(key)

    def encrypt_for_client(self, client_id: str, data: bytes) -> bytes:
        """Cifra bytes con la clave correspondiente al cliente de destino."""
        if client_id not in self.ciphers:
            raise KeyError(f"No existe clave registrada para el cliente '{client_id}'.")
        return self.ciphers[client_id].encrypt(data)

    def decrypt_for_client(self, client_id: str, token: bytes) -> bytes:
        """Descifra el token recibido con la clave del cliente remitente."""
        if client_id not in self.ciphers:
            raise KeyError(f"No existe clave registrada para el cliente '{client_id}'.")
        try:
            return self.ciphers[client_id].decrypt(token)
        except InvalidToken as e:
            raise ValueError(f"Fallo de integridad o clave incorrecta para '{client_id}': {e}")
