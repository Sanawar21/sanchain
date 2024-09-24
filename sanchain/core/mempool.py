import sqlite3
import pathlib
import base64

from ..models import Transaction, UTXO, BlockReward
from ..config import SanchainConfig


class Mempool:
    """
    Mempool class to be aggregated in SanchainCore
    """

    def __init__(self, path: pathlib.Path, config: SanchainConfig) -> None:
        self.path = path
        self.config = config

    def read_transactions(self, limit: int = None):
        """Read `limit` amount of transactions.
        By default, limit is CONFIG.block_height_limit."""

        if not limit:
            limit = self.config.block_height_limit

        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM mempool LIMIT {limit}")
            txns = []
            sanchain_sender = base64.b64encode(
                self.config.REWARD_SENDER.public_key.save_pkcs1("DER"))
            for row in cursor.fetchall():

                if row[1] != sanchain_sender:

                    # fetch input utxos via uid and output utxos via hash
                    # and append to the row

                    cursor.execute(
                        f"SELECT * FROM utxos WHERE transaction_hash = {row[6]}")
                    utxos = []
                    for utxo_row in cursor.fetchall():
                        utxos.append(UTXO.from_db_row(utxo_row))

                    cursor.execute(
                        f"SELECT * FROM utxos WHERE spender_transaction_uid = {row[0]}")
                    nascent_utxos = []
                    for nascent_utxo_row in cursor.fetchall():
                        nascent_utxos.append(
                            UTXO.from_db_row(nascent_utxo_row))

                    row = list(row)
                    row.append(nascent_utxos)
                    row.append(utxos)
                    txns.append(Transaction.from_db_row(row))
                else:

                    cursor.execute(
                        f"SELECT * FROM utxos WHERE transaction_hash = {row[6]}")
                    utxos = []
                    for utxo_row in cursor.fetchall():
                        utxos.append(UTXO.from_db_row(utxo_row))

                    cursor.execute(
                        f"SELECT * FROM utxos WHERE spender_transaction_uid = {row[0]}")
                    nascent_utxos = []
                    for nascent_utxo_row in cursor.fetchall():
                        nascent_utxos.append(
                            UTXO.from_db_row(nascent_utxo_row))

                    row = list(row)
                    row.append(nascent_utxos)
                    row.append(utxos)
                    txns.append(BlockReward.from_db_row(row))
            return txns

    def add_transaction(self, transaction: Transaction):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"INSERT INTO mempool VALUES ({', '.join(['?' for _ in range(len(Transaction.db_columns))])})",
                transaction.to_db_row()
            )

            # add spender transaction uid to the UTXOs
            for utxo in transaction.utxos:
                cursor.execute(
                    f"UPDATE utxos SET spender_transaction_uid = {transaction.uid} WHERE uid = {utxo.uid}")

            conn.commit()

    def remove_transaction(self, transaction: Transaction):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM mempool WHERE uid = {transaction.uid}")
            conn.commit()

    def update_transaction(self, transaction: Transaction):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE mempool SET {', '.join([f'{column[0]} = ?' for column in Transaction.db_columns])} WHERE uid = {transaction.uid}",
            )
