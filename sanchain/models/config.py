import pathlib
import json
from .base import AbstractBroadcastModel


class BlockChainConfig(AbstractBroadcastModel):
    PATH = pathlib.Path('.blockchain-config.json')

    def __init__(self, difficulty: int, reward: float) -> None:
        self.difficulty = difficulty
        self.reward = reward

    @classmethod
    def load_local(cls):
        if cls.PATH.exists():
            with open(cls.PATH, 'r') as file:
                return cls.from_json(json.loads(file.read()))
        else:
            # TODO: Get config from network
            return cls(4, 50.0)

    def update_local(self):
        with open(self.PATH, 'w') as file:
            file.write(json.dumps(self.to_json()))

    def to_json(self):
        return {
            'type': self.model_type,
            'difficulty': self.difficulty,
            'reward': self.reward
        }

    @classmethod
    def from_json(cls, json_data):
        return cls(
            json_data['difficulty'],
            json_data['reward']
        )
