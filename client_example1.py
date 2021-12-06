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
        # self.uri = "ws://127.0.0.1:9876/rpc/slice"
        self.ws = None

    async def connect(self):
        async with websockets.connect(self.uri, ping_interval=600) as websocket:
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

        dpg.add_texture_registry(label="Slice Map Texture Container",tag="slice_map_texture_container")
        dpg_map_image=[]
        for i in range(0,500):
            for j in range(0,500):
                dpg_map_image.append(0)
                dpg_map_image.append(0)
                dpg_map_image.append(0)
                dpg_map_image.append(1)
        dpg.add_dynamic_texture(500,500,dpg_map_image,parent="slice_map_texture_container",tag="slice_map_texture")
        volume = {
            "params":{},
            "method":"get"
        }
        await self.ws.send(mpack.pack(volume))
        frame = await self.ws.recv()
        frame = mpack.unpack(frame)
        if ("error" in frame.keys()):
            logging.error(frame["error"])
        volume_name = frame["result"]["volume_name"]
        volume_dim = frame["result"]["volume_dim"]
        volume_space = frame["result"]["volume_space"]
        logging.info(f"volume name {volume_name}, volume dim {volume_dim}, volume space {volume_space}")
        slice = {
            "params": {"slice": {"origin": [15000.0, 12000.0, 5000.0, 1.0],
                                 "normal": [0.0, 0.0, 1.0, 0.0],
                                 "right": [1.0, 0.0, 0.0, 0.0],
                                 "up": [0.0, 1.0, 0.0, 0.0],
                                 "n_pixels_width": 600,
                                 "n_pixels_height": 600,
                                 "voxel_per_pixel_width": 3,
                                 "voxel_per_pixel_height": 3},
                       "depth": 0.00032,
                       "direction": 3
                       },
            "method": "render"
        }
        slice_map = {
            "params": {"slice": slice["params"]["slice"]},
            "method": "map"
        }
        async def update_slice():
            logging.info("call update_slice")
            await self.ws.send(mpack.pack(slice))
            frame = await self.ws.recv()
            frame = mpack.unpack(frame)
            if ("error" in frame.keys()):
                logging.error(frame["error"])
                return
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

            await self.ws.send(mpack.pack(slice_map))
            frame = await self.ws.recv()
            frame = mpack.unpack(frame)
            if ("error" in frame.keys()):
                logging.error(frame["error"])
                return
            image = Image.open(io.BytesIO(frame["result"]["data"]))
            dpg_image = []
            logging.info(f"{image.width} {image.height}")
            for i in range(0, image.height):
                for j in range(0, image.width):
                    pixel = image.getpixel((j, i))
                    dpg_image.append(pixel[0] / 255)
                    dpg_image.append(pixel[1] / 255)
                    dpg_image.append(pixel[2] / 255)
                    dpg_image.append(1)
            dpg.set_value("slice_map_texture", dpg_image)

        update_slice_v = False

        def update_slice_forward():
            nonlocal update_slice_v
            update_slice_v = True
            slice["params"]["slice"]["origin"][2] = slice["params"]["slice"]["origin"][2] + 10
            dpg.set_value("origin_x", slice["params"]["slice"]["origin"][0])
            dpg.set_value("origin_y", slice["params"]["slice"]["origin"][1])
            dpg.set_value("origin_z", slice["params"]["slice"]["origin"][2])

        def update_slice_backforward():
            nonlocal update_slice_v
            update_slice_v = True
            slice["params"]["slice"]["origin"][2] = slice["params"]["slice"]["origin"][2] - 10
            dpg.set_value("origin_x", slice["params"]["slice"]["origin"][0])
            dpg.set_value("origin_y", slice["params"]["slice"]["origin"][1])
            dpg.set_value("origin_z", slice["params"]["slice"]["origin"][2])

        def update_slice_zoom_out():
            nonlocal update_slice_v
            update_slice_v = True
            slice["params"]["slice"]["voxel_per_pixel_height"] = slice["params"]["slice"][
                                                                     "voxel_per_pixel_height"] * 1.1
            slice["params"]["slice"]["voxel_per_pixel_width"] = slice["params"]["slice"]["voxel_per_pixel_width"] * 1.1
            dpg.set_value("voxels_per_pixel", slice["params"]["slice"]["voxel_per_pixel_width"])

        def update_slice_zoom_in():
            nonlocal update_slice_v
            update_slice_v = True
            slice["params"]["slice"]["voxel_per_pixel_height"] = slice["params"]["slice"][
                                                                     "voxel_per_pixel_height"] * 0.9
            slice["params"]["slice"]["voxel_per_pixel_width"] = slice["params"]["slice"]["voxel_per_pixel_width"] * 0.9
            dpg.set_value("voxels_per_pixel", slice["params"]["slice"]["voxel_per_pixel_width"])

        def update_slice_increase_depth():
            nonlocal update_slice_v
            update_slice_v = True
            depth = slice["params"]["depth"] * 1.1
            depth = max(0.0, depth)
            slice["params"]["depth"] = depth
            dpg.set_value("slice_depth", slice["params"]["depth"])

        def update_slice_decrease_depth():
            nonlocal update_slice_v
            update_slice_v = True
            depth = slice["params"]["depth"] * 0.9
            depth = max(0.0, depth)
            slice["params"]["depth"] = depth
            dpg.set_value("slice_depth", slice["params"]["depth"])

        with dpg.window(label="Information", width=200, height=600, no_resize=True, tag="slice_info"):
            with dpg.collapsing_header(label="Slice Info", default_open=True):
                dpg.add_separator()
                dpg.add_text("origin ", bullet=True, indent=20)
                dpg.add_input_float(label="x ", readonly=True, tag="origin_x")
                dpg.add_input_float(label="y ", readonly=True, tag="origin_y")
                dpg.add_input_float(label="z ", readonly=True, tag="origin_z")
                dpg.add_separator()
                dpg.add_text("voxels_per_pixel ", bullet=True, indent=20)
                dpg.add_input_float(readonly=True, tag="voxels_per_pixel")
                dpg.add_separator()
                dpg.add_text("depth ", bullet=True, indent=20)
                dpg.add_input_float(readonly=True, tag="slice_depth",format = '%.6f')
        dpg.set_value("origin_x", slice["params"]["slice"]["origin"][0])
        dpg.set_value("origin_y", slice["params"]["slice"]["origin"][1])
        dpg.set_value("origin_z", slice["params"]["slice"]["origin"][2])
        dpg.set_value("voxels_per_pixel", slice["params"]["slice"]["voxel_per_pixel_width"])
        dpg.set_value("slice_depth", slice["params"]["depth"])
        with dpg.window(label="Slice Viewer", width=600, height=600, no_resize=True, tag="slice_viewer", pos=(200, 0)):
            dpg.draw_image("slice_texture", [0, 0], [600, 600])
        with dpg.window(label="Slice Map Viewer",width=500,height=500,no_resize=True,tag="slice_map_view",pos=(800,0)):
            dpg.draw_image("slice_map_texture",[0,0],[500,500])
        with dpg.window(label="Slice Control", width=200, height=600, no_resize=True, tag="slice_control",pos=(1300, 0)):
            dpg.add_button(tag="slice_reload_forward", width=120, height=50, callback=update_slice_forward,
                           label="forward")
            dpg.add_button(tag="slice_reload_backward", width=120, height=50, label="backward",
                           callback=update_slice_backforward)
            dpg.add_button(tag="slice_reload_zoom_out", width=120, height=50, label="zoom out",
                           callback=update_slice_zoom_out)
            dpg.add_button(tag="slice_reload_zoom_in", width=120, height=50, label="zoom in",
                           callback=update_slice_zoom_in)
            dpg.add_button(tag="slice_reload_increase_depth", width=120, height=50, label="increase depth",
                           callback=update_slice_increase_depth)
            dpg.add_button(tag="slice_reload_decrease_depth", width=120, height=50, label="decrease depth",
                           callback=update_slice_decrease_depth)
        dpg.show_viewport()
        # dpg.start_dearpygui()
        while (dpg.is_dearpygui_running()):
            if update_slice_v:
                await update_slice()
                update_slice_v = False
            dpg.render_dearpygui_frame()

        dpg.destroy_context()

    def __del__(self):
        logging.info("Client obj del...")
        logging.info(f"Client is closed {self.ws.closed}")
        logging.info("destructor")


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO)
    client = Client()
    asyncio.run(client.connect())
    del client

