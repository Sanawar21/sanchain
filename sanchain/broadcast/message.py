import json
from ..models import Transaction, Block


class MessageHandler:

    types = {
        'transaction': Transaction,
        'block': Block,
    }

    def validate_message(message: str) -> bool:
        """To be used on the client side."""
        try:
            message = json.loads(message)
            assert message['type'] in MessageHandler.types
            return True
        except:
            return False

    @staticmethod
    def convert_transaction(transaction: Transaction):
        return json.dumps(transaction.to_json())

    @staticmethod
    def convert_block(block: Block):
        return json.dumps(block.to_json())

    @staticmethod
    def revert(message: str) -> Transaction | Block:
        message = json.loads(message)
        return MessageHandler.types[message['type']].from_json(message)
