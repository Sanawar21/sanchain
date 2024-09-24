import sqlite3
import os
import pathlib

from ..models import Block, Transaction, UTXO
from ..config import SanchainConfig
from .mempool import Mempool
from .utxo_set import UTXOSet


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

    def create_block(self, transactions: list[Transaction] | None = None):
        """Creates a new block with the transactions.
        By default, it will fetch the transactions from the mempool using Mempool().read_transactions"""
        if not transactions:
            transactions = self.mempool.read_transactions()
        return Block.new(transactions, self.config)

    def free_transaction_utxos(self, transaction: Transaction):
        """Frees the UTXOs of the transaction in the UTXO set.
        This is to be done when a transaction is invalid but some UTXOs have 
        been committed to it."""

        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            for utxo in transaction.utxos:
                cursor.execute(
                    f"UPDATE utxos SET spender_transaction_uid = -1 WHERE uid = {utxo.uid}")
            conn.commit()

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
