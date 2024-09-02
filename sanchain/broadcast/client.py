import websockets
from ..models import Transaction, Block
from .message import MessageHandler as MH


class Client:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.mh = MH()

    async def connect(self):
        uri = f'ws://{self.host}:{self.port}'
        self.connection = await websockets.connect(uri)

    async def send(self, message: str):
        await self.connection.send(message)

    async def listen_and_record(self):
        """
        Listen for messages and record them.
        """
        async for message in self.connection:
            if self.mh.validate_message(message):
                obj = self.mh.revert(message)
                if isinstance(obj, Transaction):
                    print("Transaction received.")
                    print(obj)
                elif isinstance(obj, Block):
                    print("Block received.")
                    print(obj)

                else:
                    print("Invalid message received.")
                    print(obj)

    async def disconnect(self):
        await self.connection.close()
