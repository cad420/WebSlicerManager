
import dearpygui.dearpygui as dpg
from dearpygui.demo import show_demo

def save_callback():
    print("Save Clicked")

if __name__ == '__main__':
    dpg.create_context()
    dpg.create_viewport()
    dpg.setup_dearpygui()

    show_demo()

    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()


