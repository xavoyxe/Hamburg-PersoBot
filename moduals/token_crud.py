import base64
import lzma
import random

def super_obfuscate(token: str) -> bytes:
    compressed = lzma.compress(token.encode())
    b85 = base64.b85encode(compressed)
    xor_key = random.randint(1, 255)
    rotated = bytes((x + 137) % 256 for x in b85)
    xored = bytes(x ^ xor_key for x in rotated)
    fake_header = bytes([random.randint(0, 255) for _ in range(8)])
    final = fake_header + bytes([xor_key]) + xored
    return final


class MegaToken:
    def __init__(self, obf_data: bytes):
        self._data = obf_data

    def __str__(self):
        return "*** SECURE ***"

    def get_token(self):
        xor_key = self._data[8]
        xored = self._data[9:]
        rotated = bytes(x ^ xor_key for x in xored)
        b85 = bytes((x - 137) % 256 for x in rotated)
        compressed = base64.b85decode(b85)
        return lzma.decompress(compressed).decode()


