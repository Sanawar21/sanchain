import sqlite3
import os
import pathlib
import base64

from ..models import Block, Transaction, UTXO, BlockReward
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


class UTXOSet:
    """
    UTXOSet class to be aggregated in SanchainCore
    """

    def __init__(self, path: pathlib.Path) -> None:
        self.path = path

    def add_utxo(self, utxo: UTXO):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"INSERT INTO utxos VALUES ({', '.join(['?' for _ in range(len(UTXO.db_columns))])})",
                utxo.to_db_row()
            )
            conn.commit()

    def remove_utxo(self, utxo: UTXO):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM utxos WHERE uid = {utxo.uid}")
            conn.commit()

    def update_utxo(self, utxo: UTXO):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE utxos SET {', '.join([f'{column[0]} = ?' for column in UTXO.db_columns])} WHERE uid = {utxo.uid}",
            )

    def fetch_by_hash(self, hash: bytes):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM utxos WHERE transaction_hash = {hash}")
            rows = cursor.fetchall()
            return [UTXO.from_db_row(row) for row in rows]

    def fetch_by_owner(self, verification_key: bytes, unused: bool = False):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            if unused:
                cursor.execute(
                    "SELECT * FROM utxos WHERE verification_key = ? AND spender_transaction_uid = -1",
                    verification_key,
                )
            else:
                cursor.execute(
                    "SELECT * FROM utxos WHERE verification_key = ?",
                    verification_key,
                )

            rows = cursor.fetchall()
            return [UTXO.from_db_row(row) for row in rows]

    def fetch_by_uid(self, uid: int):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM utxos WHERE uid = {uid}")
            row = cursor.fetchone()
            if row:
                return UTXO.from_db_row(row)
            return None


class SanchainCore:
    """
    SanchainCore is the database for the Sanchain blockchain.
    It holds the blocks, transactions, mempool and UTXO set in
    separate tables.


    Use SanchainCore.network() to fetch the blockchain from the Sanchain network.
    Use SanchainCore.local() to fetch the blockchain from the local database.
    Use SanchainCore.new() to initialize a new blockchain.
    Use SanchainCore().sync() to sync the blockchain with the network.
    Use Sanchain().delete_local() to delete the local blockchain.
    """

    DB_NAME = 'sanchainCore.db'

    def __init__(self, path: pathlib.Path, config: SanchainConfig):
        self.path = path
        self.config = config
        self.mempool = Mempool(self.path, self.config)
        self.utxo_set = UTXOSet(self.path)

    @classmethod
    def new(cls, uid: str):
        """Creates a new core without removing the previous one.
        UID is the unique identifier of the core."""
        config = SanchainConfig.default(uid)
        os.mkdir(config.DB_FOLDER / uid)
        obj = cls(config.DB_FOLDER / uid / cls.DB_NAME, config)
        obj.__create_tables()
        config.update_local_config()
        return obj

    @classmethod
    def local(cls, uid):
        """Loads the core from disk."""
        config = SanchainConfig.load_local(uid)
        obj = cls(config.DB_FOLDER / uid / cls.DB_NAME, config)
        assert os.path.exists(obj.path)
        return obj

    def __create_tables(self):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            queries = [
                f"CREATE TABLE IF NOT EXISTS blocks ({', '.join([f'{column[0]} {column[1]}' for column in Block.db_columns])})",
                f"CREATE TABLE IF NOT EXISTS transactions ({', '.join([f'{column[0]} {column[1]}' for column in Transaction.db_columns])})",
                f"CREATE TABLE IF NOT EXISTS utxos ({', '.join([f'{column[0]} {column[1]}' for column in UTXO.db_columns])})",
                f"CREATE TABLE IF NOT EXISTS mempool ({', '.join([f'{column[0]} {column[1]}' for column in Transaction.db_columns])})",
            ]
            for query in queries:
                cursor.execute(query)

    def __add_utxo(self, utxo: UTXO):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"INSERT INTO utxos VALUES ({', '.join(['?' for _ in range(len(UTXO.db_columns))])})",
                utxo.to_db_row()
            )
            conn.commit()

    def __remove_utxo(self, utxo: UTXO):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM utxos WHERE uid = {utxo.uid}")
            conn.commit()

    def __add_transaction(self, transaction: Transaction):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"INSERT INTO transactions VALUES ({', '.join(['?' for _ in range(len(Transaction.db_columns))])})",
                transaction.to_db_row()
            )
            conn.commit()

    def get_account_balance(self, verification_key: bytes):
        """Fetches the account balance from the UTXO set."""
        utxos = self.utxo_set.fetch_by_owner(verification_key, unused=True)
        return sum([utxo.value for utxo in utxos])

    def validate_utxo(self, utxo: UTXO):
        """Backtracks the UTXO to its origin and validates it."""
        # fetch transaction by id in the UTXO set
        in_set = self.utxo_set.fetch_by_uid(utxo.uid)
        return utxo == in_set

    def add_block(self, block: Block):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"INSERT INTO blocks VALUES ({', '.join(['?' for _ in range(len(Block.db_columns))])})",
                block.to_db_row()
            )
            conn.commit()

        for transaction in block.transactions:
            self.__add_transaction(transaction)

            for utxo in transaction.utxos:
                self.__remove_utxo(utxo)

            for utxo in transaction.nascent_utxos:
                self.__add_utxo(utxo)

        # TODO: Broadcast the block to the network
        # Listen for blocks
        # Validate blocks
