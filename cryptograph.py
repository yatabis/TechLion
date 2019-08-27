from base64 import b64encode, b64decode
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto import Random


def create_aes(password: str, iv: bytes) -> AES:
    sha = SHA256.new()
    sha.update(password.encode())
    key = sha.digest()
    return AES.new(key, AES.MODE_CFB, iv)


def encrypt(data: str, password: str) -> str:
    iv = Random.new().read(AES.block_size)
    return b64encode(iv + create_aes(password, iv).encrypt(data.encode())).decode()


def decrypt(data: str, password: str) -> str:
    data = b64decode(data.encode())
    iv, cipher = data[:AES.block_size], data[AES.block_size:]
    return create_aes(password, iv).decrypt(cipher).decode()
