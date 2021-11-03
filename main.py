
import dearpygui.dearpygui as dpg
from dearpygui.demo import show_demo

def save_callback():
    print("Save Clicked")

if __name__ == '__main__':
    dpg.create_context()
    dpg.create_viewport()
    dpg.setup_dearpygui()
    dpg.add_texture_registry(label="Slice Texture Container", tag="slice_texture_container")
    dpg_image = []
    for i in range(0, 600):
        for j in range(0, 600):
            dpg_image.append(1)
            dpg_image.append(0)
            dpg_image.append(1)
            dpg_image.append(1)
    dpg.add_dynamic_texture(600, 600, dpg_image, parent="slice_texture_container", tag="slice_texture")
    with dpg.window(label="Slice View",width=700,height=700):
        # dpg.add_text("hello")
        dpg.draw_image("slice_texture", [0, 0], [600, 600])
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()


