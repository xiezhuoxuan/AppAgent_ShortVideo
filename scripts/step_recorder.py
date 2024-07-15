import argparse
import datetime

# import cv2
import os
import sys
import time
from pynput import keyboard
from functools import partial

import shutil

import and_controller as ac
from and_controller import list_all_devices, AndroidController, traverse_tree, execute_adb_nowait, execute_adb
from config import load_config
from utils import print_with_color, draw_bbox_multi
from watchdog.observers import Observer
from file_watch import EventRecord_Handler, keyboard_on_press

verbose = 1

arg_desc = "AppAgent - Human Demonstration"
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=arg_desc)
parser.add_argument("--app")
parser.add_argument("--demo")
parser.add_argument("--root_dir", default="./")
parser.add_argument("--s_time")
args = vars(parser.parse_args())

app = args["app"]
demo_name = args["demo"]
root_dir = args["root_dir"]
s_time = args["s_time"]

configs = load_config()

if not app:
    print_with_color("What is the name of the app you are going to demo?", "blue")
    app = input()
    app = app.replace(" ", "")
if not demo_name:
    demo_timestamp = int(time.time())
    demo_name = datetime.datetime.fromtimestamp(demo_timestamp).strftime(f"demo_{app}_%Y-%m-%d_%H-%M-%S")

work_dir = os.path.join(root_dir, "apps")
if not os.path.exists(work_dir):
    os.mkdir(work_dir)
work_dir = os.path.join(work_dir, app)
if not os.path.exists(work_dir):
    os.mkdir(work_dir)
demo_dir = os.path.join(work_dir, "demos")
if not os.path.exists(demo_dir):
    os.mkdir(demo_dir)
task_dir = os.path.join(demo_dir, demo_name)
if os.path.exists(task_dir):
    shutil.rmtree(task_dir)
os.mkdir(task_dir)
raw_ss_dir = os.path.join(task_dir, "raw_screenshots")
os.mkdir(raw_ss_dir)
xml_dir = os.path.join(task_dir, "xml")
os.mkdir(xml_dir)
labeled_ss_dir = os.path.join(task_dir, "labeled_screenshots")
os.mkdir(labeled_ss_dir)
record_path = os.path.join(task_dir, "record.txt")
record_file = open(record_path, "w")
task_desc_path = os.path.join(task_dir, "task_desc.txt")

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
width, height = controller.get_device_size()
if not width and not height:
    print_with_color("ERROR: Invalid device size!", "red")
    sys.exit()
# print_with_color(f"Screen resolution of {device}: {width}x{height}", "yellow")

# print_with_color("Please state the goal of your following demo actions clearly, e.g. send a message to John", "blue")
# task_desc = input()
task_desc = 'Please follow these steps for each video: "If you like the current video, tap the like button. If you do not like the current video, just swipe up on the screen to proceed to the next one without tapping the like button."'
with open(task_desc_path, "w") as f:
    f.write(task_desc)

#获取坐标转换参数
ewh_size = 'event_weight_height.txt'
rw, rh = ac.get_eventwh_rate(width, height, ewh_size)

# 文件监控
f_name="envent_record.txt"
observer = Observer()
event_handler = EventRecord_Handler(f_name)
event_handler.s_time = s_time
observer.schedule(event_handler, path=".", recursive=False)
observer.start()
# 查询getevent是否被杀死的 '结果写入文件'
kill_getevent = "kill_getevent.txt"

on_press_partial = partial(keyboard_on_press, event_handler=event_handler)
listener = keyboard.Listener(on_press=on_press_partial)
listener.start()
os.system("cls")
# print("xzx"*20)
step = 0
while True:
    event_handler.ready = 0
    # print(f"000event_handler.ready: {event_handler.ready}\n")
    step += 1
    screenshot_path = controller.get_screenshot(f"{demo_name}_{step}", raw_ss_dir)
    xml_path, s_encoding = controller.get_xml(f"{demo_name}_{step}", xml_dir)
    if verbose:
        pass
        # print(f"截图已保存至{screenshot_path}\n")
        # print(f"xml文件已保存至{xml_path}\n")
    if screenshot_path == "ERROR" or xml_path == "ERROR":
        break
    clickable_list = []
    focusable_list = []
    traverse_tree(xml_path, clickable_list, "clickable", True)
    traverse_tree(xml_path, focusable_list, "focusable", True)
    elem_list = clickable_list.copy()
    for elem in focusable_list:
        bbox = elem.bbox
        center = (bbox[0][0] + bbox[1][0]) // 2, (bbox[0][1] + bbox[1][1]) // 2
        close = False
        for e in clickable_list:
            bbox = e.bbox
            center_ = (bbox[0][0] + bbox[1][0]) // 2, (bbox[0][1] + bbox[1][1]) // 2
            dist = (abs(center[0] - center_[0]) ** 2 + abs(center[1] - center_[1]) ** 2) ** 0.5
            if dist <= configs["MIN_DIST"]:
                close = True
                break
        if not close:
            elem_list.append(elem)
    labeled_img = draw_bbox_multi(screenshot_path, os.path.join(labeled_ss_dir, f"{demo_name}_{step}.png"), elem_list,
                                  True)
    
    ### 这里插入翻译官，把用户行为翻译成user_input
    adb_command = f'adb shell "nohup getevent -l 2>&1 & echo $!" >{f_name}'
    # print(adb_command)
    p = execute_adb_nowait(adb_command)
    
    my_action = ""
    my_id = -1
    if step > 1:
        print_with_color(f"请进行第 {step} 步演示！若全部演示终止请点击[e]!", "yellow")
    while 1:
        if event_handler.ready == 1:
            # print("aaa"*20)
            my_action, my_id, zb= ac.autotrans(f_name, elem_list, rw, rh)
            if verbose:
                if my_action == 'tap':
                    dt = time.time()-event_handler.a_time
                    print_with_color(f"检测到了点击！坐标为 [{zb[0]},{zb[1]}], 本次解析用时 {dt}秒", "green")
                elif my_action == 'swipe':
                    dt = time.time()-event_handler.a_time
                    print_with_color(f"检测到了滑动！起始点结束点分别为 [{zb[0]},{zb[1]}] , [{zb[2]},{zb[3]}], 本次解析用时 {dt}秒", "green")
            break
        elif event_handler.end == 1:
            # print("bbb"*20)
            my_action, my_id = 'stop', 0
            break
        # else:
        #     print("ccc"*20)
        #     time.sleep(0.3)
    # print(my_action, my_id)

    # print(f'getevent的pid: {event_handler.g_pid}\n')
    command = f"adb shell kill -9 {event_handler.g_pid}"
    command2 = f"adb shell ps | grep -w {event_handler.g_pid} >{kill_getevent}"
    result = execute_adb(command)
    while 1:
        result2 = execute_adb(command2, p=0)
        if os.stat(kill_getevent).st_size == 0:
            # print(f"杀死getevent{event_handler.g_pid}成功\n")
            break
        time.sleep(0.01)
    p.kill()
    # os.remove(f_name)
    user_input = my_action
    if user_input.lower() == "tap":
        user_input = my_id
        record_file.write(f"tap({int(user_input)}):::{elem_list[int(user_input) - 1].uid}\n")
        
    elif user_input.lower() == "swipe":
        # 默认设置为up，直接只能向上滑
        user_input = "up"
        swipe_dir = user_input
        user_input = my_id
        record_file.write(f"swipe({int(user_input)}:sep:{swipe_dir}):::{elem_list[int(user_input) - 1].uid}\n")
    elif user_input.lower() == "stop":
        record_file.write("stop\n")
        record_file.close()
        print_with_color("整个流程结束！", "green")
        break
    else:
        break
    # time.sleep(0.1)

observer.stop()
print_with_color(f"演示完成，总共记录了 {step-1} 步。", "green")

# 清楚临时文件
file_list = [ewh_size, kill_getevent, f_name]
for filename in file_list:
    os.remove(filename)
