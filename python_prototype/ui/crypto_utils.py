import os
import hashlib
import hmac

_APP_SECRET = b"Cardflow_S3cur3_K3y_2026!"
_IV_LEN = 16

_MACHINE_KEY = None

def _get_machine_key():
    global _MACHINE_KEY
    if _MACHINE_KEY is None:
        machine_id = os.environ.get('COMPUTERNAME', 'UNKNOWN')
        _MACHINE_KEY = hashlib.sha256(_APP_SECRET + machine_id.encode()).digest()
    return _MACHINE_KEY

def _xor_stream(data, key, iv):
    result = bytearray()
    counter = 0
    offset = 0
    while offset < len(data):
        counter_bytes = counter.to_bytes(8, 'big')
        keystream = hmac.new(key, iv + counter_bytes, 'sha256').digest()
        chunk = data[offset:offset + 32]
        for i, b in enumerate(chunk):
            result.append(b ^ keystream[i])
        offset += 32
        counter += 1
    return bytes(result)

def encrypt_file(filepath):
    if not os.path.exists(filepath):
        return
    try:
        with open(filepath, 'rb') as f:
            plaintext = f.read()
    except Exception:
        return
    iv = os.urandom(_IV_LEN)
    file_key = hashlib.sha256(_get_machine_key() + iv).digest()
    ciphertext = _xor_stream(plaintext, file_key, iv)
    with open(filepath, 'wb') as f:
        f.write(b'CRD0' + iv + ciphertext)

def decrypt_to_file(filepath):
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
    except Exception:
        return None
    if len(data) < 4 + _IV_LEN or data[:4] != b'CRD0':
        return None
    iv = data[4:4 + _IV_LEN]
    ciphertext = data[4 + _IV_LEN:]
    file_key = hashlib.sha256(_get_machine_key() + iv).digest()
    plaintext = _xor_stream(ciphertext, file_key, iv)
    with open(filepath, 'wb') as f:
        f.write(plaintext)
    return plaintext

def encrypt_path(filepath):
    if not os.path.exists(filepath):
        return
    try:
        with open(filepath, 'rb') as f:
            header = f.read(4)
        if header == b'CRD0':
            return
    except Exception:
        pass
    encrypt_file(filepath)

def decrypt_path(filepath):
    if not os.path.exists(filepath):
        return
    try:
        with open(filepath, 'rb') as f:
            header = f.read(4)
        if header != b'CRD0':
            return
    except Exception:
        return
    decrypt_to_file(filepath)
