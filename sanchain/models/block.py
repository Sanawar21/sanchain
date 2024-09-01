import rsa
import time
import random
import json
import base64

from ..config import SanchainConfig
from ..utils import CONFIG
from .transaction import Transaction, BlockReward
from ..base import AbstractSanchainModel


class Block(AbstractSanchainModel):
    """
    Use Block.new() to create a new block for mining.
    """

    db_columns = [
        ('idx', 'INTEGER PRIMARY KEY'),
        ('timestamp', 'INTEGER'),
        ('merkle_root', 'BLOB'),
        ('hash', 'BLOB'),
        ('nonce', 'INTEGER'),
        # add config data
        ('version', 'INTEGER'),
        ('difficulty', 'INTEGER'),
        ('reward', 'REAL'),
        ('block_UTXO_usage_limit', 'INTEGER'),
        ('miner_fees', 'REAL'),
        ('block_height_limit', 'INTEGER'),
        ('last_block_index', 'INTEGER'),
        ('last_block_hash', 'BLOB'),
        ('circulation', 'REAL'),
    ]

    def __init__(self, idx: int, timestamp: int, merkle_root: bytes, config: SanchainConfig, transactions: list[Transaction], hash: bytes, nonce: int) -> None:
        self.idx = idx
        self.timestamp = timestamp
        self.merkle_root = merkle_root
        self.config = config
        self.transactions = transactions
        self.hash = hash
        self.nonce = nonce
        self.invalid_transactions = []

    @classmethod
    def new(cls, transactions: list[Transaction]):
        return cls(
            CONFIG.last_block_index + 1,
            0,
            b'',
            CONFIG,
            transactions,
            b'',
            0,
        )

    @classmethod
    def from_json(cls, json_data):
        return cls(
            json_data['timestamp'],
            base64.b64decode(json_data['merkle_root'].encode()),
            SanchainConfig.from_json(json_data['config']),
            [Transaction.from_json(transaction)
             for transaction in json_data['transactions']],
            base64.b64decode(json_data['hash'].encode()),
            json_data['nonce'],
        )

    @classmethod
    def from_db_row(cls, row):
        return cls(
            row[0],
            row[1],
            row[2],
            SanchainConfig(
                row[5],
                row[6],
                row[7],
                row[8],
                row[9],
                row[10],
                row[11],
                row[12],
                row[13],
            ),
            [],  # TODO: load transactions from database
            row[3],
            row[4],

        )

    def to_json(self):
        return {
            'idx': self.idx,
            'timestamp': self.timestamp,
            'merkle_root': base64.b64encode(self.merkle_root).decode(),
            'hash': base64.b64encode(self.hash).decode(),
            'nonce': self.nonce,
            'transactions': [transaction.to_json() for transaction in self.transactions],
            'config': self.config.to_json(),
        }

    def to_db_row(self):
        return (
            self.idx,
            self.timestamp,
            self.merkle_root,
            self.hash,
            self.nonce,
            # add config data
            self.config.version,
            self.config.difficulty,
            self.config.reward,
            self.config.block_UTXO_usage_limit,
            self.config.miner_fees,
            self.config.block_height_limit,
            self.config.last_block_index,
            self.config.last_block_hash,
            self.config.circulation,
        )

    def __calculate_merkle_root(self):
        nodes = [transaction.hash for transaction in self.transactions]

        while len(nodes) > 1:

            new_nodes = []

            for i in range(0, len(nodes), 2):
                try:
                    new_nodes.append(rsa.compute_hash(
                        nodes[i] + nodes[i + 1], 'SHA-256'))
                except IndexError:
                    new_nodes.append(rsa.compute_hash(nodes[i]), 'SHA-256')

            nodes = new_nodes

        return nodes[-1]

    def __calculate_hash(self, block_data: bytes):
        nonce = random.randint(0, 99999999999999999)
        proof = b'0' * self.config.difficulty
        hash = b''
        while not hash.startswith(proof):
            nonce += 1
            hash = rsa.compute_hash(block_data +
                                    nonce.to_bytes(8, 'little'), 'SHA-256')
        return hash, nonce

    def mine(self, miner: rsa.PublicKey):

        self.timestamp = int(time.time())

        # verify and execute transactions
        for transaction in self.transactions:
            if transaction.verify():
                transaction.execute(miner)
            else:
                self.invalid_transactions.append(transaction)

        for transaction in self.invalid_transactions:
            self.transactions.remove(transaction)

        self.transactions.append(BlockReward.new(miner))

        # calculate merkle hash
        self.merkle_root = self.__calculate_merkle_root()

        block = self.to_json()

        # remove hash key
        del block['hash']
        del block['nonce']

        block_data = json.dumps(block).encode()
        hash, nonce = self.__calculate_hash(block_data)

        self.hash = hash
        self.nonce = nonce

        # TODO: broadcast block
