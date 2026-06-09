# signature.py
import json
import base64
import os
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization

def load_or_generate_keys(service_name):
    priv_path = f"{service_name}_private.pem"
    pub_path = f"{service_name}_public.pem"

    if os.path.exists(priv_path) and os.path.exists(pub_path):
        with open(priv_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(key_file.read(), password=None)
        with open(pub_path, "rb") as key_file:
            public_key = serialization.load_pem_public_key(key_file.read())
        return private_key, public_key

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    with open(priv_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    with open(pub_path, "wb") as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
    return private_key, public_key

def sign_event(private_key, data):
    data_str = json.dumps(data, sort_keys=True)
    signature = private_key.sign(
        data_str.encode('utf-8'),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode('utf-8')

def validate_signature(public_key, data, signature_b64):
    try:
        signature_bytes = base64.b64decode(signature_b64)
        data_str = json.dumps(data, sort_keys=True)
        public_key.verify(
            signature_bytes,
            data_str.encode('utf-8'),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False