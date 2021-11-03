import asyncio
import websockets
import json
from PIL import Image
import io
import mpack
import dearpygui.dearpygui as dpg
import logging
import threading


class Client:

    def __init__(self):
        self.uri = "ws://127.0.0.1:16689/rpc/slice"
        self.ws = None

    async def connect(self):
        async with websockets.connect(self.uri, ping_interval=60) as websocket:
            self.ws = websocket
            logging.info(self.ws.open)
            await self.run()
    async def run(self):
        logging.info(f"start run and ws is open {self.ws.open}")
        dpg.create_context()
        dpg.create_viewport()
        dpg.setup_dearpygui()
        dpg.add_texture_registry(label="Slice Texture Container", tag="slice_texture_container")
        dpg_image = []
        for i in range(0, 600):
            for j in range(0, 600):
                dpg_image.append(0)
                dpg_image.append(0)
                dpg_image.append(0)
                dpg_image.append(1)
        dpg.add_dynamic_texture(600, 600, dpg_image, parent="slice_texture_container", tag="slice_texture")
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

        async def update_slice():
            logging.info("call update_slice")
            await self.ws.send(mpack.pack(slice))
            frame = await self.ws.recv()
            frame = mpack.unpack(frame)
            image = Image.open(io.BytesIO(frame["result"]["data"]))
            dpg_image = []
            for i in range(0, image.height):
                for j in range(0, image.width):
                    pixel = image.getpixel((j, i))
                    dpg_image.append(pixel[0] / 255)
                    dpg_image.append(pixel[1] / 255)
                    dpg_image.append(pixel[2] / 255)
                    dpg_image.append(1)
            dpg.set_value("slice_texture", dpg_image)
            slice["params"]["Slice"]["origin"][2] = slice["params"]["Slice"]["origin"][2] + 100
        update_slice_v = False

        def set_update_slice():
           nonlocal update_slice_v
           update_slice_v = True

        with dpg.window(label="Slice Viewer", width=600, height=600, no_resize=True, tag="slice_viewer"):
            dpg.draw_image("slice_texture", [0, 0], [600, 600])
        with dpg.window(label="Slice Control",width=200,height=600,no_resize=True,tag="slice_control"):
            dpg.add_button(tag="slice_reload",width=50,height=50,callback=set_update_slice)
        dpg.show_viewport()
        # dpg.start_dearpygui()
        while(dpg.is_dearpygui_running()):
            if update_slice_v:
                await update_slice()
                update_slice_v = False
            dpg.render_dearpygui_frame()

        dpg.destroy_context()

    def __del__(self):
        logging.info("Client obj del...")
        logging.info(f"Client is closed {self.ws.closed}")
        logging.info("destructor")


async def hello():
    # uri = "ws://127.0.0.1:9876/rpc/slice" # connect to manager
    uri = "ws://127.0.0.1:16689/rpc/slice" # connect directly to server
    ws = None
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
        try:
            while True:
                await websocket.send(mpack.pack(slice))
                frame = await websocket.recv()
                frame = mpack.unpack(frame)
                image = Image.open(io.BytesIO(frame["result"]["data"]))
                dpg_image = []
                for i in range(0, image.height):
                    for j in range(0, image.width):
                        pixel = image.getpixel((j, i))
                        dpg_image.append(pixel[0] / 255)
                        dpg_image.append(pixel[1] / 255)
                        dpg_image.append(pixel[2] / 255)
                        dpg_image.append(1)
                dpg.set_value("slice_texture",dpg_image)
                slice["params"]["Slice"]["origin"][2] = slice["params"]["Slice"]["origin"][2]+100
        except websockets.exceptions.ConnectionClosed:
            logging.info(f"websocket connection {websocket.id} closed")
        finally:
            logging.info("websocket connection close")
        # await websocket.send(mpack.pack(slice))
        #
        # frame = await websocket.recv()
        # frame = mpack.unpack(frame)
        # print(type(frame))
        # print(f"received from manager: {frame}")
        # await websocket.send("hello again")
        # frame = await websocket.recv()
        # print(f"received from manager again: {frame}")
        # greeting = await asyncio.wait_for(websocket.recv(),timeout=70)
        # image = Image.frombytes("L",(600,600),frame["result"]["data"])
        # image = Image.open(io.BytesIO(frame["result"]["data"]))
        # image.show("Slice")
if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO)
    client = Client()
    asyncio.run(client.connect())
    del client

