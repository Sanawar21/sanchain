import json
from ..models.transaction import Transaction
from ..models.block import Block
from ..utils import SanchainConfig


class MessageHandler:
    @staticmethod
    def convert_transaction(transaction: Transaction):
        return json.dumps(transaction.to_json())

    @staticmethod
    def convert_block(block: Block):
        return json.dumps(block.to_json())

    @staticmethod
    def revert(message: str) -> Transaction | Block | SanchainConfig:
        return Transaction.from_json(json.loads(message))
