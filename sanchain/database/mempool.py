from ..models.transaction import Transaction


class Mempool:

    def get_oldest(self) -> list[Transaction]:
        return [
            Transaction()
        ]
