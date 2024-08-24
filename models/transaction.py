from uuid import uuid4
import rsa
import json


class Transaction:

    def __init__(self, sender_pubkey, receiver_pubkey, amount) -> None:
        self.uid = uuid4().int
        self.sender_pubkey = sender_pubkey
        self.receiver_pubkey = receiver_pubkey
        self.amount = amount

    def to_json(self):
        return {
            'uid': self.uid,
            'sender_pubkey': self.sender_pubkey.save_pkcs1().decode(),
            'receiver_pubkey': self.receiver_pubkey.save_pkcs1().decode(),
            'amount': self.amount,
        }

    @classmethod
    def from_json(cls, json_data):
        transaction = cls(
            rsa.PublicKey.load_pkcs1(json_data['sender_pubkey'].encode()),
            rsa.PublicKey.load_pkcs1(json_data['receiver_pubkey'].encode()),
            json_data['amount'],
        )
        transaction.uid = json_data['uid']
        return transaction


class SignedTransaction:

    def __init__(self, transaction: Transaction, signature: bytes) -> None:
        self.transaction = transaction
        self.signature = signature

    def to_json(self):
        return {
            'transaction': self.transaction.to_json(),
            'signature': self.signature.hex(),
        }

    @classmethod
    def from_json(cls, json_data):
        transaction = Transaction.from_json(json_data['transaction'])
        signature = bytes.fromhex(json_data['signature'])
        return cls(transaction, signature)
