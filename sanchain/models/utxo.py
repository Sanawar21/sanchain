import rsa
import json
import base64

from .base import AbstractBroadcastModel, AbstractDatabaseModel


class UTXO(AbstractDatabaseModel, AbstractBroadcastModel):
    def __init__(self, verification_key: bytes, value, index: int, transaction_hash: bytes) -> None:
        # hash of the owner public key
        self.verification_key = verification_key
        self.value = value
        self.index = index
        self.transaction_hash = transaction_hash

    def sign(self, private_key: rsa.PrivateKey):
        self.signature = rsa.sign(json.dumps(
            self.to_json()).encode(), private_key, 'SHA-256')

    def verify(self, pubkey: rsa.PublicKey) -> bool:
        pubkey_hash = rsa.compute_hash(pubkey.save_pkcs1('DER'), 'SHA-256')
        if pubkey_hash != self.verification_key:
            return False

        try:
            rsa.verify(json.dumps(self.to_json()).encode(),
                       self.signature, pubkey)
        except rsa.VerificationError:
            return False
        else:
            return True

    def to_json(self):
        return {
            'verification_key': base64.b64encode(self.verification_key).decode(),
            'value': self.value,
            'index': self.index,
            'transaction_hash': base64.b64encode(self.transaction_hash).decode(),
        }

    @classmethod
    def from_json(cls, json_data):
        return cls(
            base64.b64decode(json_data['verification_key']),
            json_data['value'],
            json_data['index'],
            base64.b64decode(json_data['transaction_hash']),
        )
    # TODO: Figure out storing these in database, sharing of unsigned UTXOs, and broadcasting of signed UTXOs
