from nacl import exceptions as nacl_exceptions
from nacl import signing


class SigningKey:
    def __init__(self, sk_s: bytes):
        if len(sk_s) == 64:
            seed = sk_s[:32]
        elif len(sk_s) == 32:
            seed = sk_s
        else:
            raise ValueError("invalid signing key length")

        self._signing_key = signing.SigningKey(seed)
        self._verifying_key = self._signing_key.verify_key
        self.sk_s = seed + bytes(self._verifying_key)

    def get_verifying_key(self):
        return VerifyingKey(vk_s=bytes(self._verifying_key))

    def sign(self, msg: bytes) -> bytes:
        return self._signing_key.sign(msg).signature


class VerifyingKey:
    def __init__(self, vk_s: bytes):
        if len(vk_s) != 32:
            raise ValueError("invalid verifying key length")

        self._verify_key = signing.VerifyKey(vk_s)
        self.vk_s = bytes(vk_s)

    def verify(self, sig: bytes, msg: bytes):
        try:
            self._verify_key.verify(msg, sig)
        except nacl_exceptions.BadSignatureError as exc:
            raise ValueError("bad signature") from exc


def create_keypair():
    sk = SigningKey(signing.SigningKey.generate().encode())
    return sk, sk.get_verifying_key()
