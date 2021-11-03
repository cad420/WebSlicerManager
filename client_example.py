import asyncio
import websockets
import json
from PIL import Image
import io
import mpack
async def hello():
    uri = "ws://127.0.0.1:9876/rpc/slice" # connect to manager
    # uri = "ws://127.0.0.1:16689/rpc/slice" # connect directly to server
    async with websockets.connect(uri,ping_interval=60) as websocket:
        slice={
            "params":{"Slice": {"origin": [15000.0, 12000.0, 5000.0, 1.0],
                       "normal": [0.0, 0.0, 1.0, 0.0],
                       "right": [1.0, 0.0, 0.0, 0.0],
                       "up": [0.0, 1.0, 0.0, 0.0],
                       "n_pixels_width": 600,
                       "n_pixels_height": 600,
                       "voxel_per_pixel_width": 3,
                       "voxel_per_pixel_height": 3}},
            "method":"render"
        }
        # await websocket.ping()
        await websocket.send(mpack.pack(slice))

        frame = await websocket.recv()
        frame = mpack.unpack(frame)
        print(type(frame))
        # print(f"received from manager: {frame}")
        # await websocket.send("hello again")
        # frame = await websocket.recv()
        # print(f"received from manager again: {frame}")
        # greeting = await asyncio.wait_for(websocket.recv(),timeout=70)
        # image = Image.frombytes("L",(600,600),frame["result"]["data"])
        image = Image.open(io.BytesIO(frame["result"]["data"]))
        image.show("Slice")
asyncio.run(hello())