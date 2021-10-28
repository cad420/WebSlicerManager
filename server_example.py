import asyncio
import websockets
import json
async def client_t(msg: str,handler):
    uri = "ws://127.0.0.1:16689/rpc"
    async with websockets.connect(uri,ping_interval=70) as websocket:

        await websocket.send(msg)
        # print(f">>> {name}")

        greeting = await websocket.recv()
        # greeting = await asyncio.wait_for(websocket.recv(),timeout=70)
        print(type(greeting))

        handler(greeting)
        return
async def serve_t(websocket,path):
    if(path == '/rpc'):
        print("client connect to manager")
    elif(path == '/worker'):
        print("backend worker connect to manager")

    name = await websocket.recv()
    print(f"manager receive request from client: {name}")
    greeting=list()
    def handler(msg:str):
        greeting.append(msg);
    await client_t(name,handler)
    await websocket.send(greeting[0])

async def main():
    async with websockets.serve(serve_t,"localhost",8765):
        await asyncio.Future()
if __name__ == "__main__":
    asyncio.run(main())
