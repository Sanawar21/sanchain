import pathlib
import json
import base64
import os
import sqlite3

from .models.account import Account  # prevents circular import
from .base import AbstractSanchainModel


class SanchainConfig(AbstractSanchainModel):
    DB_FOLDER = pathlib.Path(os.getcwd()) / 'data'
    REWARD_SENDER = Account.from_json(
        {
            'public_key': 'MEgCQQCT7Caq7rTxn+ZbpY2CkTvactkiQvLO8SiZdiR5BIl0YreoOIvtJI5UL5LcXbQFikvA0KIHptBlmGFqi+Us5GKNAgMBAAE=',
            'private_key': 'MIIBOwIBAAJBAJPsJqrutPGf5luljYKRO9py2SJC8s7xKJl2JHkEiXRit6g4i+0kjlQvktxdtAWKS8DQogem0GWYYWqL5SzkYo0CAwEAAQJAGtv6eXc2q9kY/vMkqtysPZI1Ex+M7z6i3JqzLLZCBCMkE8TFe5XJlXdpC3pOFaR71lUN62kL9Ko26RTcaWQ+AQIjAO1Y/TT10iN2lPvys/YGlBi5xgKIMAW9IXprvylJwOlnKGECHwCfjBZdv/cQwkTWchq10KH0BkMpScXIItRSzaYAua0CIgdsmy8G6XXWhb6DzwFJH2TOmtUFcYscaWms6SPffLtQUMECHknsIUzMrc+RA04Mzj1hbjhfUmzl5oKlSJUY/YomfQIibQB+ZEqSKq8yHz1lIsO0oh5B0gfWYBM5fx0MXA/r7Rbe+w==',
        }

    )

    db_columns = [
        ('version', 'INTEGER PRIMARY KEY'),
        ('difficulty', 'INTEGER'),
        ('reward', 'REAL'),
        ('block_UTXO_usage_limit', 'INTEGER'),
        ('miner_fees', 'REAL'),
        ('block_height_limit', 'INTEGER'),
        ('last_block_index', 'INTEGER'),
        ('last_block_hash', 'BLOB'),
        ('circulation', 'REAL'),
    ]

    def __init__(self, core_id, version, difficulty: int, reward: float, block_UTXO_usage_limit: int, miner_fees: float, block_height_limit: int, last_block_index: int, last_block_hash: bytes, circulation: float) -> None:
        self.core_id = core_id
        self.version = version
        self.difficulty = difficulty
        self.reward = reward
        self.block_UTXO_usage_limit = block_UTXO_usage_limit
        self.miner_fees = miner_fees
        self.block_height_limit = block_height_limit
        self.last_block_index = last_block_index
        self.last_block_hash = last_block_hash
        self.circulation = circulation

        self.path = self.__get_path(self.core_id)

    @classmethod
    def __get_path(cls, core_id):
        return pathlib.Path(
            cls.DB_FOLDER / core_id / '.Sanchain-config.json')

    @classmethod
    def default(cls, core_id):
        return cls(core_id, 1, 3, 100.0, 1000, 0.01, 100, -1, b'', 0.0)

    @classmethod
    def load_local(cls, core_id):
        path = cls.__get_path(core_id)
        if path.exists():
            with open(path, 'r') as file:
                return cls.from_json(json.loads(file.read()), core_id)
        else:
            # TODO: Get config from network
            return cls.default(core_id)

    def refresh(self):
        """Refreshes the config from the local file."""
        self = self.load_local()

    def update_wrt_recent_block(self, block):
        """
        Updates the config parameters with respect to the recent block
        both locally and for self.
        """
        self.last_block_index = block.idx
        self.last_block_hash = block.hash
        # last transaction is the reward transaction
        self.circulation += block.transactions[-1].amount

        self.update_local_config()

    def update_local_config(self):
        """Changes the local config to self."""
        with open(self.path, 'w') as file:
            file.write(json.dumps(self.to_json()))

    def to_json(self):
        return {
            'type': self.model_type,
            'version': self.version,
            'difficulty': self.difficulty,
            'reward': self.reward,
            'block_UTXO_usage_limit': self.block_UTXO_usage_limit,
            'miner_fees': self.miner_fees,
            'block_height_limit': self.block_height_limit,
            'last_block_index': self.last_block_index,
            'last_block_hash': base64.b64encode(self.last_block_hash).decode(),
            'circulation': self.circulation,
        }

    @classmethod
    def from_json(cls, json_data, core_id):
        return cls(
            core_id,
            json_data['version'],
            json_data['difficulty'],
            json_data['reward'],
            json_data['block_UTXO_usage_limit'],
            json_data['miner_fees'],
            json_data['block_height_limit'],
            json_data['last_block_index'],
            base64.b64decode(json_data['last_block_hash']),
            json_data['circulation'],
        )

    def to_db_row(self):
        return (
            self.version,
            self.difficulty,
            self.reward,
            self.block_UTXO_usage_limit,
            self.miner_fees,
            self.block_height_limit,
            self.last_block_index,
            sqlite3.Binary(self.last_block_hash),
            self.circulation,
        )

    @classmethod
    def from_db_row(cls, row, core_id):
        return cls(
            core_id,
            row[0],
            row[1],
            row[2],
            row[3],
            row[4],
            row[5],
            row[6],
            row[7],
            row[8],
        )
