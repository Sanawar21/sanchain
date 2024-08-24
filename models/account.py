import rsa
import json
from .transaction import Transaction, SignedTransaction


class Account:
    def __init__(self) -> None:
        self.public_key, self.private_key = rsa.newkeys(512)

    def to_json(self):
        return {
            'public_key': self.public_key.save_pkcs1().decode(),
            'private_key': self.private_key.save_pkcs1().decode()
        }

    @classmethod
    def from_json(cls, json_data):
        account = cls()
        account.public_key = rsa.PublicKey.load_pkcs1(
            json_data['public_key'].encode()
        )
        account.private_key = rsa.PrivateKey.load_pkcs1(
            json_data['private_key'].encode()
        )
        return account

    def sign_transaction(self, transaction: Transaction):
        signature = rsa.sign(
            json.dumps(transaction.to_json()).encode(),
            self.private_key,
            'SHA-256'
        )
        return SignedTransaction(transaction, signature)

    @staticmethod
    def verify_signature(signed_transaction: SignedTransaction):
        try:
            rsa.verify(
                json.dumps(signed_transaction.transaction.to_json()).encode(),
                signed_transaction.signature,
                signed_transaction.transaction.sender_pubkey
            )
        except rsa.VerificationError:
            return False
        else:
            return True
