import rsa
import base64

from ..base import AbstractBroadcastModel


class Account(AbstractBroadcastModel):
    """
    Use Account.new() to create a new account.
    """

    def __init__(self, public_key: rsa.PublicKey, private_key: rsa.PrivateKey) -> None:
        self.public_key = public_key
        self.private_key = private_key
        self.verification_key = rsa.compute_hash(
            public_key.save_pkcs1("DER"), "SHA-256"),

    @classmethod
    def new(cls):
        return cls(*rsa.newkeys(512))

    @classmethod
    def from_json(cls, json_data: dict):
        return cls(
            rsa.PublicKey.load_pkcs1(base64.b64decode(
                json_data['public_key']), format="DER"),
            rsa.PrivateKey.load_pkcs1(base64.b64decode(
                json_data['private_key']), format="DER"),
        )

    def to_json(self):
        return {
            'public_key': base64.b64encode(self.public_key.save_pkcs1("DER")).decode(),
            'private_key': base64.b64encode(self.private_key.save_pkcs1("DER")).decode()
        }

    @property
    def balance(self):
        # TODO: Implement this
        return 0
