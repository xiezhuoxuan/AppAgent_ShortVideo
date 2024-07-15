# @file initial.py
# @brief 初始化项目所需环境
# @author Zhuoxuan Xie
# @email 1206852606@qq.com
# @date 2024-06-15

from and_controller import AndroidController, list_all_devices
from utils import print_with_color
import sys
import os

os.system("cls")
print_with_color("开始初始化. . .", "yellow")
device_list = list_all_devices()
if not device_list:
    print_with_color("ERROR: No device found!", "red")
    sys.exit()
# print_with_color("List of devices attached:\n" + str(device_list), "yellow")
if len(device_list) == 1:
    device = device_list[0]
    # print_with_color(f"Device selected: {device}", "yellow")
else:
    print_with_color("Please choose the Android device to start demo by entering its ID:", "blue")
    device = input()
controller = AndroidController(device)

# 主要是运行一次以下函数，这样可以在虚拟机上启动所需环境
screenshot_path = controller.get_screenshot(f"initial", "./")
xml_path, s_encoding = controller.get_xml(f"initial", "./")

os.remove(screenshot_path)
os.remove(xml_path)

print_with_color("初始化完毕!", "yellow")