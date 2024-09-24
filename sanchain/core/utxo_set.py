import sqlite3
import pathlib

from ..models import UTXO


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
