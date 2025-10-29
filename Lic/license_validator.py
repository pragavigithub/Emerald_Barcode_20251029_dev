# license_validator.py
import json, base64, datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

def load_public_key(pem_path_or_bytes):
    from cryptography.hazmat.backends import default_backend
    if isinstance(pem_path_or_bytes, bytes):
        data = pem_path_or_bytes
    else:
        data = open(pem_path_or_bytes,"rb").read()
    return serialization.load_pem_public_key(data)

def validate_license_file(license_file_path, public_key):
    raw = open(license_file_path, "rb").read()
    data = json.loads(raw)
    payload_b64 = data.get("payload")
    sig_b64 = data.get("signature")
    if not payload_b64 or not sig_b64:
        return False, "Invalid license format"

    payload = base64.b64decode(payload_b64)
    sig = base64.b64decode(sig_b64)

    # Verify signature
    try:
        public_key.verify(
            sig,
            payload,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
    except InvalidSignature:
        return False, "Signature verification failed"

    # Parse payload
    payload_json = json.loads(payload.decode("utf-8"))
    from_date = datetime.datetime.fromisoformat(payload_json["from"])
    to_date = datetime.datetime.fromisoformat(payload_json["to"])
    now = datetime.datetime.utcnow()
    if now < from_date:
        return False, f"License not active until {from_date}"
    if now > to_date + datetime.timedelta(days=1):
        return False, "License expired"

    # Optionally check product, name etc
    return True, payload_json

# Example usage
if __name__ == "__main__":
    # public key can be packaged as bytes into the exe to avoid external file
    pub = load_public_key("public_key.pem")
    ok, info = validate_license_file("license.lic", pub)
    print(ok, info)
