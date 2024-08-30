import websockets


class Client:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

    async def connect(self):
        uri = f'ws://{self.host}:{self.port}'
        self.connection = await websockets.connect(uri)

    async def send(self, message: str):
        await self.connection.send(message)

    async def receive(self):
        return await self.connection.recv()

    async def disconnect(self):
        await self.connection.close()
