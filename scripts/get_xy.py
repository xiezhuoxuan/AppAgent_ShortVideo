# @file get_xy.py
# @brief 在Agent完成学习后，检查其学习是否正确并持久化所需元素的坐标，加速实际模拟阶段的操作
# @author Zhuoxuan Xie
# @email 1206852606@qq.com
# @date 2024-06-15

import sys
from and_controller import AndroidController, traverse_tree, list_all_devices
from utils import print_with_color, draw_bbox_multi
import datetime
import time
import os
import prompts as prompts
import re
from model import QwenModel, parse_explore_rsp
from config import load_config
import ast
import yaml

device_list = list_all_devices()
if not device_list:
    print_with_color("ERROR: No device found!", "red")
    sys.exit()
# print_with_color(f"List of devices attached:\n{str(device_list)}", "yellow")
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

configs = dict(os.environ)
with open("./config.yaml", "r") as file:
    yaml_data = yaml.safe_load(file)
configs.update(yaml_data)

mllm = QwenModel(api_key=configs["DASHSCOPE_API_KEY"],
                    model=configs["QWEN_MODEL"])

task_desc = 'Please follow these steps for each video: "If you like the current video, tap the like button. If you do not like the current video, just swipe up on the screen to proceed to the next video."'
app = 'blbl'

root_dir="./"
app_dir = os.path.join(os.path.join(root_dir, "raw_apps"), app)
work_dir = os.path.join(root_dir, "tasks")
if not os.path.exists(work_dir):
    os.mkdir(work_dir)
task_timestamp = int(time.time())
dir_name = datetime.datetime.fromtimestamp(task_timestamp).strftime(f"getxy_{app}_%Y-%m-%d_%H-%M-%S")
task_dir = os.path.join(work_dir, dir_name)
os.mkdir(task_dir)

screenshot_path = controller.get_screenshot(f"{dir_name}_get_xy", task_dir)
xml_path, s_encoding = controller.get_xml(f"{dir_name}_get_xy", task_dir)

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

auto_docs_dir = os.path.join(app_dir, "auto_docs")
demo_docs_dir = os.path.join(app_dir, "demo_docs")
no_doc = False
if not os.path.exists(auto_docs_dir) and not os.path.exists(demo_docs_dir):
    print_with_color(f"No documentations found for the app {app}. Do you want to proceed with no docs? Enter y or n",
                     "red")
    user_input = ""
    while user_input != "y" and user_input != "n":
        user_input = input().lower()
    if user_input == "y":
        no_doc = True
    else:
        sys.exit()
elif os.path.exists(auto_docs_dir) and os.path.exists(demo_docs_dir):
    print_with_color(f"The app {app} has documentations generated from both autonomous exploration and human "
                     f"demonstration. Which one do you want to use? Type 1 or 2.\n1. Autonomous exploration\n2. Human "
                     f"Demonstration",
                     "blue")
    user_input = ""
    while user_input != "1" and user_input != "2":
        user_input = input()
    if user_input == "1":
        docs_dir = auto_docs_dir
    else:
        docs_dir = demo_docs_dir
elif os.path.exists(auto_docs_dir):
    # print_with_color(f"Documentations generated from autonomous exploration were found for the app {app}. The doc base "
    #                  f"is selected automatically.", "yellow")
    docs_dir = auto_docs_dir
else:
    # print_with_color(f"Documentations generated from human demonstration were found for the app {app}. The doc base is "
    #                  f"selected automatically.", "yellow")
    docs_dir = demo_docs_dir

ui_doc = ""
for i, elem in enumerate(elem_list):
    doc_path = os.path.join(docs_dir, f"{elem.uid}.txt")
    if not os.path.exists(doc_path):
        continue
    # 读取之前生成的说明书
    ui_doc += f"Documentation of UI element labeled with the numeric tag '{i + 1}':\n"
    doc_content = ast.literal_eval(open(doc_path, "r").read())
    if doc_content["tap"]:
        ui_doc += f"This UI element is clickable. {doc_content['tap']}\n\n"
    if doc_content["text"]:
        ui_doc += f"This UI element can receive text input. The text input is used for the following " \
                f"purposes: {doc_content['text']}\n\n"
    if doc_content["long_press"]:
        ui_doc += f"This UI element is long clickable. {doc_content['long_press']}\n\n"
    if doc_content["v_swipe"]:
        ui_doc += f"This element can be swiped directly without tapping. You can swipe vertically on " \
                f"this UI element. {doc_content['v_swipe']}\n\n"
    if doc_content["h_swipe"]:
        ui_doc += f"This element can be swiped directly without tapping. You can swipe horizontally on " \
                f"this UI element. {doc_content['h_swipe']}\n\n"
# print_with_color(f"Documentations retrieved for the current interface:\n{ui_doc}", "magenta")
ui_doc = """
You also have access to the following documentations that describes the functionalities of UI 
elements you can interact on the screen. These docs are crucial for you to determine the target of your 
next action. You should always prioritize these documented elements for interaction:""" + ui_doc

draw_bbox_multi(screenshot_path, os.path.join(task_dir, f"{dir_name}_getxy_labeled.png"), elem_list,
                        dark_mode=configs["DARK_MODE"])
image = os.path.join(task_dir, f"{dir_name}_getxy_labeled.png")

# 执行点赞操作
prompt_action = prompts.task_template_action
prompt_action = re.sub(r"<ui_document>", ui_doc, prompt_action)
prompt_action = re.sub(r"<task_description>", task_desc, prompt_action)
prompt_action = re.sub(r"<like>", 'like', prompt_action)
status, rsp = mllm.get_model_response(prompt_action, [image])
res = parse_explore_rsp(rsp, 1, 'action', 0)
# print(res)
act_name = res[0]
if act_name == "tap":
    _, area = res
    tl, br = elem_list[area - 1].bbox
    # 获取点击控件的中心坐标
    xt, yt = (tl[0] + br[0]) // 2, (tl[1] + br[1]) // 2
    ret = controller.tap(xt, yt)
    with open("tap_swipe_coordinate.txt", 'w') as f:
        f.write(f"{xt}\t{yt}\n")

# 执行上滑操作
prompt_action = prompts.task_template_action
prompt_action = re.sub(r"<ui_document>", ui_doc, prompt_action)
prompt_action = re.sub(r"<task_description>", task_desc, prompt_action)
prompt_action = re.sub(r"<like>", 'dislike', prompt_action)
status, rsp = mllm.get_model_response(prompt_action, [image])
res = parse_explore_rsp(rsp, 1, 'action', 0)
# print(res)
act_name = res[0]
if act_name == "swipe":
    _, area, swipe_dir, dist = res
    tl, br = elem_list[area - 1].bbox
    # 获取滑动控件的中心坐标
    xs, ys = (tl[0] + br[0]) // 2, (tl[1] + br[1]) // 2
    ret = controller.swipe(xs, ys, swipe_dir, dist)
    with open("tap_swipe_coordinate.txt", 'a') as f:
        f.write(f"{xs}\t{ys}\n")
# with open("tap_swipe.txt")
print_with_color(f"点赞控件的坐标为 [{xt},{yt}]", "green")
print_with_color(f"上滑控件的坐标为 [{xs},{ys}]", "green")