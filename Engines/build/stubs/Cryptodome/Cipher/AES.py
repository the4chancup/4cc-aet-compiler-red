# Minimal AES stub for py7zr when encryption is not needed
class AESCipherStub:
    MODE_CBC = 2

    def __init__(self, key, mode, iv):
        raise RuntimeError("AES encryption not supported in this distribution")

    def encrypt(self, data):
        raise RuntimeError("AES encryption not supported in this distribution")

    def decrypt(self, data):
        raise RuntimeError("AES encryption not supported in this distribution")

def new(key, mode, iv):
    return AESCipherStub(key, mode, iv)
