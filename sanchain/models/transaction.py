import rsa
import base64
import json
import sqlite3

from ..utils import uid
from ..config import SanchainConfig
from ..base import AbstractSanchainModel
from .utxo import UTXO
# from ..core import SanchainCore


class Transaction(AbstractSanchainModel):
    """Transaction that can be signed and will be broadcasted
    to the mempool.
    Use Transaction.unsigned() to create a new unsigned transaction as client and sign it yourself.
    Use Transaction() to verify a transaction from the mempool yourself as a miner.

    A verified transaction will be hashed and new UTXOs will be generated.
    """

    db_columns = [
        ('uid', 'INTEGER PRIMARY KEY'),
        ('sender', 'BLOB'),
        ('receiver', 'BLOB'),
        ('amount', 'REAL'),
        ('signature', 'BLOB'),
        ('hash', 'BLOB'),
        ('block_index', 'INTEGER'),
    ]

    def __init__(self, uid: int, sender: rsa.PublicKey, receiver: rsa.PublicKey, amount: float, utxos: list[UTXO], signature: bytes, nascent_utxos: list[UTXO], hash: bytes, block_index: int) -> None:
        self.uid = uid
        self.sender = sender
        self.receiver = receiver
        self.amount = float(amount)
        self.utxos = utxos  # input utxos
        self.signature = signature

        self.nascent_utxos = nascent_utxos  # output utxos
        self.hash = hash

        self.block_index = block_index

        self.__is_verified = False

    @classmethod
    def unsigned(cls, sender: rsa.PublicKey, receiver: rsa.PublicKey, amount: float, utxos: list[UTXO]):
        return cls(uid(), sender, receiver, float(amount), utxos, b'', [], b'', -1)

    @classmethod
    def from_db_row(cls, row):
        obj = cls(
            row[0],
            rsa.PublicKey.load_pkcs1(base64.b64decode(row[1]), format="DER"),
            rsa.PublicKey.load_pkcs1(base64.b64decode(row[2]), format="DER"),
            float(row[3]),
            row[-2],  # use uid to fetch the UTXOs from the database
            row[4],
            row[-1],  # use hash to fetch the UTXOs from the database
            row[5],
            row[6],
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
            float(json_data['amount']),
            [UTXO.from_json(utxo) for utxo in json_data['utxos']],
            base64.b64decode(json_data['signature']),
            [UTXO.from_json(utxo) for utxo in json_data['nascent_utxos']],
            base64.b64decode(json_data['hash']),
            json_data['block_index'],
        )

    def to_db_row(self):
        return (
            self.uid,
            sqlite3.Binary((base64.b64encode(self.sender.save_pkcs1("DER")))),
            sqlite3.Binary(base64.b64encode(self.receiver.save_pkcs1("DER"))),
            float(self.amount),
            sqlite3.Binary(self.signature),
            sqlite3.Binary(self.hash),
            self.block_index,
        )

    def to_json(self):
        return {
            'type': self.model_type,
            'uid': self.uid,
            'sender': base64.b64encode(self.sender.save_pkcs1("DER")).decode(),
            'receiver': base64.b64encode(self.receiver.save_pkcs1("DER")).decode(),
            'amount': float(self.amount),
            'signature': base64.b64encode(self.signature).decode(),
            'utxos': [utxo.to_json() for utxo in self.utxos],
            'nascent_utxos': [utxo.to_json() for utxo in self.nascent_utxos],
            'hash': base64.b64encode(self.hash).decode(),
            'block_index': self.block_index,
        }

    def signable(self):
        data = self.to_json()

        del data['signature']
        del data['nascent_utxos']
        del data['hash']
        del data['block_index']

        utxo_without_spender = []
        for utxo in self.utxos:
            utxo_without_spender.append(utxo.to_json())
            del utxo_without_spender[-1]['spender_transaction_uid']

        data['utxos'] = utxo_without_spender
        return data

    def sign(self, private_key: rsa.PrivateKey):
        # at this point, the transaction will contain only the
        # sender, receiver, amount and utxos
        # so remove everything else and sign the transaction
        # when verifying, remove everything else and verify the signature

        data = self.signable()

        self.signature = rsa.sign(
            json.dumps(data).encode(),
            private_key,
            'SHA-256'
        )

    def verify(self, config: SanchainConfig):
        """Verify the transaction and its utxos."""
        try:
            data = self.signable()

            rsa.verify(
                json.dumps(data).encode(),
                self.signature,
                self.sender
            )

            # verify the utxos
            for utxo in self.utxos:
                assert utxo.verification_key == rsa.compute_hash(
                    self.sender.save_pkcs1("DER"), "SHA-256")

            # TODO: verify the utxos from the blockchain by backtracking

            # verify the balance
            assert sum([utxo.value for utxo in self.utxos]) >= (
                self.amount + self.amount * config.miner_fees), "Insufficient balance"

        except (rsa.VerificationError, KeyError, AssertionError):
            self.__is_verified = False
            return False
        else:
            self.__is_verified = True
            return True

    def execute(self, miner: rsa.PublicKey, config: SanchainConfig):
        """Complete a transaction by creating new outputs as NascentUTXOs.
        This method should be called after the transaction has been verified.
        """
        assert self.__is_verified, "Transaction must be verified first"

        self.block_index = config.last_block_index + 1
        input_amount = sum([utxo.value for utxo in self.utxos])

        self.nascent_utxos = [
            UTXO.nascent(  # miner's fees
                rsa.compute_hash(miner.save_pkcs1("DER"), "SHA-256"),
                self.amount * config.miner_fees,
                0,
                self.block_index,
            ),
            UTXO.nascent(  # receiver's utxo
                rsa.compute_hash(self.receiver.save_pkcs1("DER"), "SHA-256"),
                self.amount,
                1,
                self.block_index,
            ),
        ]

        # return change, if any
        change = input_amount - self.amount

        if change > 0:
            self.nascent_utxos.append(  # sender's change
                UTXO.nascent(
                    rsa.compute_hash(self.sender.save_pkcs1("DER"), "SHA-256"),
                    change,
                    2,
                    self.block_index,
                )
            )

        # hash the transaction
        self.hash = rsa.compute_hash(json.dumps(
            self.to_json()).encode(), "SHA-256")

        for utxo in self.nascent_utxos:
            utxo.transaction_hash = self.hash


class BlockReward(Transaction):
    """Block reward transaction for the miner.
    Use BlockReward.new() to create a new block reward transaction as a miner.
    """

    @classmethod
    def new(cls, miner: rsa.PublicKey, config: SanchainConfig):
        obj = cls(
            uid(),
            config.REWARD_SENDER.public_key,
            miner,
            config.reward,
            [],  # input utxos
            b'',  # signature
            [UTXO.nascent(
                rsa.compute_hash(miner.save_pkcs1("DER"), "SHA-256"),
                config.reward,
                0,
                config.last_block_index + 1,
            )],  # nascent utxos (output)
            b'',  # hash
            config.last_block_index + 1,
        )
        obj.hash = rsa.compute_hash(json.dumps(
            obj.to_json()).encode(), "SHA-256")
        for utxo in obj.nascent_utxos:
            utxo.transaction_hash = obj.hash
        obj.sign(config.REWARD_SENDER.private_key)
        return obj
