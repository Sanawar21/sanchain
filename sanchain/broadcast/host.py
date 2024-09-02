import asyncio
import websockets


clients = []


async def server(websocket, path):
    clients.append(websocket)
    print(f"{websocket.remote_address} connected.")
    try:
        async for message in websocket:
            for client in clients:
                await client.send(message)
    except websockets.ConnectionClosed:
        print(f"{websocket.remote_address} disconnected.")

    finally:
        clients.remove(websocket)

if __name__ == "__main__":
    HOST = "localhost"
    PORT = 8765

    start_server = websockets.serve(server, HOST, PORT)
    print(f"Server started at ws://{HOST}:{PORT}")
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
