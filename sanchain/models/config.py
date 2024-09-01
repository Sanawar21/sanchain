import pathlib
import json
import base64
from .base import AbstractBroadcastModel, AbstractDatabaseModel


class SanchainConfig(AbstractBroadcastModel, AbstractDatabaseModel):
    PATH = pathlib.Path('.Sanchain-config.json')
    REWARD_SENDER = 'SANCHAIN'

    def __init__(self, version, difficulty: int, reward: float, block_UTXO_usage_limit: int, miner_fees: float, block_height_limit: int, last_block_index: int, last_block_hash: bytes, circulation: float) -> None:
        self.version = version
        self.difficulty = difficulty
        self.reward = reward
        self.block_UTXO_usage_limit = block_UTXO_usage_limit
        self.miner_fees = miner_fees
        self.block_height_limit = block_height_limit
        self.last_block_index = last_block_index
        self.last_block_hash = last_block_hash
        self.circulation = circulation

    @property
    def db_columns(self):
        return [
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

    @classmethod
    def default(cls):
        return cls(1, 4, 100.0, 10, 0.01, 1000, -1, b'', 0.0)

    @classmethod
    def load_local(cls):
        if cls.PATH.exists():
            with open(cls.PATH, 'r') as file:
                return cls.from_json(json.loads(file.read()))
        else:
            # TODO: Get config from network
            return cls.default()

    def update_local(self):
        with open(self.PATH, 'w') as file:
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
    def from_json(cls, json_data):
        return cls(
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
            self.last_block_hash,
            self.circulation,
        )

    @classmethod
    def from_db_row(cls, row):
        return cls(
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
