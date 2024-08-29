import rsa
import base64
import json

from ..utils import generate_uid
from .base import AbstractBroadcastModel, AbstractDatabaseModel


class Transaction(AbstractDatabaseModel, AbstractBroadcastModel):
    """
    A transaction between two accounts.
    Use Transaction.unsigned() to create a new unsigned transaction. 
    """

    def __init__(self, uid, sender: rsa.PublicKey, receiver: rsa.PublicKey, amount: float, signature: bytes) -> None:
        self.uid = uid
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.signature = signature

    @classmethod
    def unsigned(cls, sender: rsa.PublicKey, receiver: rsa.PublicKey, amount: float):
        return cls(generate_uid(), sender, receiver, amount, b'')

    def sign(self, private_key: rsa.PrivateKey):
        self.signature = rsa.sign(
            json.dumps(self.to_json()).encode(),
            private_key,
            'SHA-256'
        )

    def verify(self):
        try:
            data = self.to_json()
            # remove signature
            del data['signature']

            rsa.verify(
                data.encode(),
                self.signature,
                self.sender
            )
        except (rsa.VerificationError, KeyError):
            return False
        else:
            return True

    def to_json(self):
        return {
            'type': self.model_type,
            'uid': self.uid,
            'sender': base64.b64encode(self.sender.save_pkcs1("DER")).decode(),
            'receiver': base64.b64encode(self.receiver.save_pkcs1("DER")).decode(),
            'amount': self.amount,
            'signature': base64.b64encode(self.signature).decode(),
        }

    @classmethod
    def from_json(cls, json_data):
        transaction = cls(
            rsa.PublicKey.load_pkcs1(base64.b64decode(
                json_data['sender']), format="DER"),
            rsa.PublicKey.load_pkcs1(base64.b64decode(
                json_data['receiver']), format="DER"),
            json_data['amount'],
            base64.b64decode(json_data['signature'])
        )
        transaction.uid = json_data['uid']
        return transaction

    def as_db_row(self):
        return (
            self.uid,
            self.sender.save_pkcs1("DER"),
            self.receiver.save_pkcs1("DER"),
            self.amount,
            self.signature
        )

    @classmethod
    def from_db_row(cls, row):
        return cls(
            rsa.PublicKey.load_pkcs1(row[1], format="DER"),
            rsa.PublicKey.load_pkcs1(row[2], format="DER"),
            row[3],
            row[4]
        )

    @property
    def db_columns(self):
        return [
            ('uid', 'INTEGER PRIMARY KEY'),
            ('sender', 'BLOB'),
            ('receiver', 'BLOB'),
            ('amount', 'REAL'),
            ('signature', 'BLOB'),
        ]


class ValidTransaction(Transaction):
    """A transaction that has been validated by a miner and added to 
    a block. It contains additional information about the block it is in.
    """
    # TODO: Add spent UTXOs
    # TODO: Remove spent UTXOs from the sender on the database
    # TODO: Add newly created UTXOs for sender, receiver and miner
