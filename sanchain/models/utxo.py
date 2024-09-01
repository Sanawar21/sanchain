import base64

from ..base import AbstractSanchainModel
from ..utils import uid


class UTXO(AbstractSanchainModel):
    db_columns = [
        ('uid', 'INTEGER PRIMARY KEY'),
        ('verification_key', 'BLOB'),
        ('value', 'REAL'),
        ('idx', 'INTEGER'),
        ('transaction_hash', 'BLOB'),
        ('block_index', 'INTEGER'),
        ('spender_transaction_uid', 'INTEGER'),
    ]

    def __init__(self, uid: int, verification_key: bytes, value: float, idx: int, transaction_hash: bytes, block_index: int,  spender_transaction_uid: int) -> None:
        self.uid = uid
        # hash of the owner public key
        self.verification_key = verification_key
        self.value = value
        self.idx = idx
        self.transaction_hash = transaction_hash
        self.block_index = block_index
        self.spender_transaction_uid = spender_transaction_uid

    @classmethod
    def nascent(cls, verification_key: bytes, value: float, idx: int, block_index: int):
        return cls(uid(), verification_key, value, idx, b'', block_index, -1)

    @classmethod
    def from_json(cls, data):
        return cls(
            data['uid'],
            base64.b64decode(data['verification_key']),
            data['value'],
            data['idx'],
            base64.b64decode(data['transaction_hash']),
            data['block_index'],
            data['spender_transaction_uid'],
        )

    def to_json(self):
        return {
            'type': self.model_type,
            'uid': self.uid,
            'verification_key': base64.b64encode(self.verification_key).decode(),
            'value': self.value,
            'idx': self.idx,
            'transaction_hash': base64.b64encode(self.transaction_hash).decode(),
            'block_index': self.block_index,
            'spender_transaction_uid': self.spender_transaction_uid,
        }

    def to_db_row(self):
        return (
            self.uid,
            self.verification_key,
            self.value,
            self.idx,
            self.transaction_hash,
            self.block_index,
            self.spender_transaction_uid,
        )

    @classmethod
    def from_db_row(cls, row):
        return cls(*row)
