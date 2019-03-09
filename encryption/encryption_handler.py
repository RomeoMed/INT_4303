import base64
import hashlib
import json
from crypto import Random
from crypto.Cipher import AES


with open('secret.json') as shh:
    secret = json.load(shh)
_key = secret.get('password_key')


class AESCipher(object):
    def __init__(self):
        self.bs = 32
        self.key = hashlib.sha256(_key.encode()).digest()

    def encrypt(self, plaintext: str):
        plaintext = self._pad(plaintext)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)

        return base64.b64encode(iv + cipher.encrypt(plaintext))

    def decrypt(self, encrypted: str):
        encrypted = base64.b64decode(encrypted)
        iv = encrypted[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)

        return self._unpad(cipher.decrypt(encrypted[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]