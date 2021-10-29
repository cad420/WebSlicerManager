# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import asyncio

def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')
    l=dict()
    l[1]=2;
    l[3]=2
    for item in l.items():
        item[1]=3
        print(item[0],item[1])
    s = "/slice/1"
    info = s.strip('/').split('/')
    print(info)
    l=list()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
