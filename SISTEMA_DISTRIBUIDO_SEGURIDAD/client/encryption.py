"""
Módulo de seguridad y cifrado Fernet para el Cliente.
Permite cifrar y descifrar cargas útiles mediante cifrado simétrico con integridad autenticada.
"""

import os
from cryptography.fernet import Fernet, InvalidToken

class ClientSecurityManager:
    def __init__(self, client_id: str, key: bytes = None, key_file: str = None):
        self.client_id = client_id
        if key is not None:
            self.key = key if isinstance(key, bytes) else key.encode('utf-8')
        elif key_file and os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                self.key = f.read().strip()
        else:
            # Buscar en directorio local de claves
            default_key_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                f".{client_id}.key"
            )
            if os.path.exists(default_key_path):
                with open(default_key_path, 'rb') as f:
                    self.key = f.read().strip()
            else:
                # Generar nueva clave
                self.key = Fernet.generate_key()
                with open(default_key_path, 'wb') as f:
                    f.write(self.key)
        
        self.cipher = Fernet(self.key)

    def encrypt(self, data: bytes) -> bytes:
        """Cifra bytes utilizando la clave simétrica del cliente."""
        return self.cipher.encrypt(data)

    def decrypt(self, token: bytes) -> bytes:
        """Descifra el token recibido del servidor."""
        try:
            return self.cipher.decrypt(token)
        except InvalidToken as e:
            raise ValueError(f"Fallo de descifrado/autenticación para {self.client_id}: {e}")

    def get_key(self) -> bytes:
        return self.key
