import rsa
from .transaction import Transaction


class Account:
    def __init__(self) -> None:
        self.public_key, self.private_key = rsa.newkeys(512)

    @property
    def balance(self):
        # TODO: Implement this
        return 0

    def mine_block(self):
        pass
