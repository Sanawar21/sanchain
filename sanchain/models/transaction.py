import rsa
import base64
import json

from ..utils import generate_uid, CONFIG
from .base import AbstractBroadcastModel, AbstractDatabaseModel
from .utxo import UTXO


class Transaction(AbstractBroadcastModel, AbstractDatabaseModel):
    """Transaction that can be signed and will be broadcasted
    to the mempool.
    Use Transaction.unsigned() to create a new unsigned transaction as client and sign it yourself.
    Use Transaction() to verify a transaction from the mempool yourself as a miner.

    A verified transaction will be hashed and new UTXOs will be generated.
    """

    def __init__(self, uid: int, sender: rsa.PublicKey, receiver: rsa.PublicKey, amount: float, utxos: list[UTXO], signature: bytes, nascent_utxos: list[UTXO], hash: bytes) -> None:
        self.uid = uid
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.utxos = utxos
        self.signature = signature

        self.nascent_utxos = nascent_utxos
        self.hash = hash
        self.__is_verified = False

    @property
    def db_columns(self):
        return [
            ('uid', 'INTEGER PRIMARY KEY'),
            ('sender', 'BLOB'),
            ('receiver', 'BLOB'),
            ('amount', 'REAL'),
            ('signature', 'BLOB'),
            ('hash', 'BLOB'),
        ]

    @classmethod
    def unsigned(cls, sender: rsa.PublicKey, receiver: rsa.PublicKey, amount: float, utxos: list[UTXO]):
        return cls(generate_uid(), sender, receiver, amount, utxos, b'', [], b'')

    @classmethod
    def from_db_row(cls, row):
        obj = cls(
            row[0],
            rsa.PublicKey.load_pkcs1(base64.b64decode(row[1]), format="DER"),
            rsa.PublicKey.load_pkcs1(base64.b64decode(row[2]), format="DER"),
            row[3],
            [],  # use uid to fetch the UTXOs from the database
            row[4],
            [],  # use hash to fetch the UTXOs from the database
            row[5],
        )
        # TODO: fetch the UTXOs from the database
        return obj

    @classmethod
    def from_json(cls, json_data):
        return cls(
            json_data['uid'],
            rsa.PublicKey.load_pkcs1(base64.b64decode(
                json_data['sender']), format="DER"),
            rsa.PublicKey.load_pkcs1(base64.b64decode(
                json_data['receiver']), format="DER"),
            json_data['amount'],
            [UTXO.from_json(utxo) for utxo in json_data['utxos']],
            base64.b64decode(json_data['signature']),
            [UTXO.from_json(utxo) for utxo in json_data['nascent_utxos']],
            base64.b64decode(json_data['hash']),
        )

    def to_db_row(self):
        return (
            self.uid,
            base64.b64encode(self.sender.save_pkcs1("DER")),
            base64.b64encode(self.receiver.save_pkcs1("DER")),
            self.amount,
            self.signature,
            self.hash,
        )

    def to_json(self):
        return {
            'type': self.model_type,
            'uid': self.uid,
            'sender': base64.b64encode(self.sender.save_pkcs1("DER")).decode(),
            'receiver': base64.b64encode(self.receiver.save_pkcs1("DER")).decode(),
            'amount': self.amount,
            'signature': base64.b64encode(self.signature).decode(),
            'utxos': [utxo.to_json() for utxo in self.utxos],
            'nascent_utxos': [utxo.to_json() for utxo in self.nascent_utxos],
            'hash': base64.b64encode(self.hash).decode(),
        }

    def sign(self, private_key: rsa.PrivateKey):
        # at this point, the transaction will contain only the
        # sender, receiver, amount and utxos
        # so remove everything else and sign the transaction
        # when verifying, remove everything else and verify the signature
        data = self.to_json()

        del data['signature']
        del data['nascent_utxos']
        del data['hash']

        self.signature = rsa.sign(
            json.dumps(data).encode(),
            private_key,
            'SHA-256'
        )

    def verify_signature(self):
        """Verify the transaction and its utxos."""
        try:
            # verify the transaction itself
            data = self.to_json()

            # prepare the data for verification
            del data['signature']
            del data['nascent_utxos']
            del data['hash']

            rsa.verify(
                data.encode(),
                self.signature,
                self.sender
            )

            # verify the utxos
            for utxo in self.utxos:
                assert utxo.verification_key == rsa.compute_hash(
                    self.sender, "SHA-256")

            # TODO: verify the utxos from the blockchain by backtracking

            # verify the balance
            assert sum([utxo.value for utxo in self.utxos]) >= (
                self.amount + self.amount * CONFIG.miner_fees), "Insufficient balance"

        except (rsa.VerificationError, KeyError, AssertionError):
            self.__is_verified = True
            return False
        else:
            self.__is_verified = True
            return True

    def execute(self, miner: rsa.PublicKey):
        """Complete a transaction by creating new outputs as NascentUTXOs.
        This method should be called after the transaction has been verified.
        """
        assert self.__is_verified

        self.nascent_utxos = [
            UTXO.nascent(  # receiver's utxo
                rsa.compute_hash(self.receiver, "SHA-256"),
                self.amount,
                0
            ),
            UTXO.nascent(  # miner's fees
                rsa.compute_hash(miner, "SHA-256"),
                self.amount * CONFIG.miner_fee,
                1
            ),
        ]

        # return change, if any
        change = self.amount - sum([utxo.value for utxo in self.nascent_utxos])

        if change > 0:
            self.nascent_utxos.append(  # sender's change
                UTXO.nascent(
                    rsa.compute_hash(self.sender, "SHA-256"),
                    change,
                    2
                )
            )

        # hash the transaction
        self.hash = rsa.compute_hash(json.dumps(
            self.to_json()).encode(), "SHA-256")

        # TODO: Add the hash to the nascent UTXOs in the database
