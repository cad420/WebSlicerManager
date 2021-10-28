import asyncio
import websockets
import json
from PIL import Image
async def hello():
    uri = "ws://127.0.0.1:8765/rpc"
    async with websockets.connect(uri,ping_interval=70) as websocket:
        slice={
            "slice":{"origin": [15000.0, 12000.0, 5000.0, 1.0],
             "normal": [0.0, 0.0, 1.0, 0.0],
             "right": [1.0, 0.0, 0.0, 0.0],
             "up": [0.0, 1.0, 0.0, 0.0],
             "n_pixels_width": 600,
             "n_pixels_height": 600,
             "voxel_per_pixel_width": 2,
             "voxel_per_pixel_height": 2}
        }
        await websocket.send(json.dumps(slice))

        frame = await websocket.recv()
        # greeting = await asyncio.wait_for(websocket.recv(),timeout=70)
        image = Image.frombytes("L",(600,600),frame)
        image.show("Slice")
asyncio.run(hello())