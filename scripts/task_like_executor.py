# @file run_like.py
# @brief 在假设一个用户喜欢所有视频的场景下，进行行为模拟，测试及演示使用
# @author Zhuoxuan Xie
# @email 1206852606@qq.com
# @date 2024-06-15

import argparse
import ast
import datetime
import json
import os
import re
import sys
import time
import requests

import prompts, my_prompts
from config import load_config
from and_controller import list_all_devices, AndroidController, traverse_tree
from model import parse_explore_rsp, parse_grid_rsp, my_parse_explore_rsp, my_parse_grid_rsp, OpenAIModel, QwenModel
from utils import print_with_color, draw_bbox_multi, draw_grid
os.system("cls")
# time.sleep(5)

verbose = 1
arg_desc = "AppAgent Executor"
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=arg_desc)
parser.add_argument("--app")
parser.add_argument("--root_dir", default="./")
args = vars(parser.parse_args())

configs = load_config()

if configs["MODEL"] == "OpenAI":
    mllm = OpenAIModel(base_url=configs["OPENAI_API_BASE"],
                       api_key=configs["OPENAI_API_KEY"],
                       model=configs["OPENAI_API_MODEL_TEXTONLY"],
                       temperature=configs["TEMPERATURE"],
                       max_tokens=configs["MAX_TOKENS"])
elif configs["MODEL"] == "Qwen":
    mllm = QwenModel(api_key=configs["DASHSCOPE_API_KEY"],
                     model=configs["QWEN_MODEL"])
else:
    print_with_color(f"ERROR: Unsupported model type {configs['MODEL']}!", "red")
    sys.exit()

# mllm_qw = QwenModel(api_key=configs["DASHSCOPE_API_KEY"],
#                      model=configs["QWEN_MODEL"])

app = args["app"]
root_dir = args["root_dir"]

if not app:
    print_with_color("What is the name of the app you want me to operate?", "blue")
    app = input()
    app = app.replace(" ", "")

app_dir = os.path.join(os.path.join(root_dir, "raw_apps"), app)
work_dir = os.path.join(root_dir, "tasks")
if not os.path.exists(work_dir):
    os.mkdir(work_dir)
auto_docs_dir = os.path.join(app_dir, "auto_docs")
demo_docs_dir = os.path.join(app_dir, "demo_docs")
task_timestamp = int(time.time())
dir_name = datetime.datetime.fromtimestamp(task_timestamp).strftime(f"task_{app}_%Y-%m-%d_%H-%M-%S")
task_dir = os.path.join(work_dir, dir_name)
os.mkdir(task_dir)
log_path = os.path.join(task_dir, f"log_{app}_{dir_name}.txt")
my_log_path = os.path.join(task_dir, f"mylog_{app}_{dir_name}.txt")
user_desc_path = os.path.join(task_dir, f"user_desc.txt")

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
# print_with_color(f"Screen resolution of {device}: {width}x{height}", "yellow")

# print_with_color("Please enter the description of the task you want me to complete in a few sentences:", "blue")
task_desc = 'Please follow these steps for each video: "If you like the current video, tap the like button. If you do not like the current video, just swipe up on the screen to proceed to the next video."'
# task_desc = input()
# print_with_color("Please enter the description of the user you want me to impersonate in a few sentences:", "blue")
user_desc = "like basketball, pets, doesn't like other topics."
user_dislike = ["sport, basketball", "pet, dog", "pet, tortoise", "sport, NBA"]
user_like = ["plot, love", "knowledge, economics", "game, moba", "knowledge, car", "read, history"]
# user_desc = input()

tmp_list = []
with open("tap_swipe_coordinate.txt", 'r') as f:
    for l in f.readlines():
        if len(l) > 0:
            l = l.strip('\n').split('\t')
            tmp_list.append(int(l[0]))
            tmp_list.append(int(l[1]))
xt, yt, xs, ys = tmp_list

round_count = 0
# last_summary = ""
# last_act = ""
task_complete = False
grid_on = False
rows, cols = 0, 0
new_video = True
def area_to_xy(area, subarea):
    area -= 1
    row, col = area // cols, area % cols
    x_0, y_0 = col * (width // cols), row * (height // rows)
    if subarea == "top-left":
        x, y = x_0 + (width // cols) // 4, y_0 + (height // rows) // 4
    elif subarea == "top":
        x, y = x_0 + (width // cols) // 2, y_0 + (height // rows) // 4
    elif subarea == "top-right":
        x, y = x_0 + (width // cols) * 3 // 4, y_0 + (height // rows) // 4
    elif subarea == "left":
        x, y = x_0 + (width // cols) // 4, y_0 + (height // rows) // 2
    elif subarea == "right":
        x, y = x_0 + (width // cols) * 3 // 4, y_0 + (height // rows) // 2
    elif subarea == "bottom-left":
        x, y = x_0 + (width // cols) // 4, y_0 + (height // rows) * 3 // 4
    elif subarea == "bottom":
        x, y = x_0 + (width // cols) // 2, y_0 + (height // rows) * 3 // 4
    elif subarea == "bottom-right":
        x, y = x_0 + (width // cols) * 3 // 4, y_0 + (height // rows) * 3 // 4
    else:
        x, y = x_0 + (width // cols) // 2, y_0 + (height // rows) // 2
    return x, y
# print_with_color(f"user profile: {user_desc}","green")
# with open(user_desc_path, 'w') as f:
#     f.write(user_desc)
    
while round_count < configs["MAX_ROUNDS"] or not new_video:
    if new_video:
        round_count += 1
        print_with_color(f"Round {round_count}", "green")
        time.sleep(3)
    if new_video:
        screenshot_path = controller.get_screenshot(f"{dir_name}_{round_count}", task_dir)
        xml_path, s_encoding = controller.get_xml(f"{dir_name}_{round_count}", task_dir)
        if verbose:
            print(f"截图已保存至{screenshot_path}\n")
            print(f"xml文件已保存至{xml_path}\n")
    else:
        screenshot_path = controller.get_screenshot(f"{dir_name}_{round_count}_action2", task_dir)
        xml_path, s_encoding = controller.get_xml(f"{dir_name}_{round_count}_action2", task_dir)
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
    
    if new_video:
        draw_bbox_multi(screenshot_path, os.path.join(task_dir, f"{dir_name}_{round_count}_labeled.png"), elem_list,
                        dark_mode=configs["DARK_MODE"])
        image = os.path.join(task_dir, f"{dir_name}_{round_count}_labeled.png")
        
        ##understand
        prompt_understand = prompts.task_template_understand
        if verbose:
            print_with_color('正在进行图文理解. . .\n','yellow')
        status, rsp = mllm.get_model_response(prompt_understand, [image])
        res = parse_explore_rsp(rsp, new_video, 'understand')
        # print(rsp)
        # print(res)
        viewing = res[0]
        title = res[1]
        ##likeornot_loacl
        # prompt_likeornot = prompts.task_template_likeornot
        # prompt_likeornot = re.sub(r"<viewing>", viewing, prompt_likeornot)
        # prompt_likeornot = re.sub(r"<title>", title, prompt_likeornot)
        # prompt_likeornot = re.sub(r"<user_description>", user_desc, prompt_likeornot)
        # status, rsp = mllm.get_model_response(prompt_likeornot, [])
        # res = parse_explore_rsp(rsp, new_video, 'likeornot')
        # reason = res[0]
        # like = res[1]

        ##likeornot_romote_agent
        if verbose:
            print_with_color("根据图文理解分析是否偏好. . .\n",'yellow')
        
        # url = 'http://10.61.1.25:8989/islike'
        # headers = {'Content-Type': 'application/json'}
        # data = {'like_historys': user_like, 'dislike_historys': user_dislike,  'target_item': viewing+" the title is "+title}
        # response = requests.post(url, json=data, headers=headers)
        # # print(response.text)
        # like = response.json()['isLiker']['like']
        # reason = response.json()['isLiker']['reason']
        
        # if int(time.time()) % 2 == 0:
        #     like = "like"
        #     reason = "1.时间为偶数\n2.随机生成原因\n3.啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦"
        # else:
        #     like = "dislike"
        #     reason = "1.时间为奇数\n2.随机生成原因\n3.哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈"
        
        like = "like"
        print_with_color(like, 'green')
        reason = ""
        # print("Reason: "+reason.replace('\n', " ") + "\n")
        ## action
        # ui_doc = ""
        # for i, elem in enumerate(elem_list):
        #     doc_path = os.path.join(docs_dir, f"{elem.uid}.txt")
        #     if not os.path.exists(doc_path):
        #         continue
        #     ui_doc += f"Documentation of UI element labeled with the numeric tag '{i + 1}':\n"
        #     doc_content = ast.literal_eval(open(doc_path, "r").read())
        #     if doc_content["tap"]:
        #         ui_doc += f"This UI element is clickable. {doc_content['tap']}\n\n"
        #     if doc_content["text"]:
        #         ui_doc += f"This UI element can receive text input. The text input is used for the following " \
        #                 f"purposes: {doc_content['text']}\n\n"
        #     if doc_content["long_press"]:
        #         ui_doc += f"This UI element is long clickable. {doc_content['long_press']}\n\n"
        #     if doc_content["v_swipe"]:
        #         ui_doc += f"This element can be swiped directly without tapping. You can swipe vertically on " \
        #                 f"this UI element. {doc_content['v_swipe']}\n\n"
        #     if doc_content["h_swipe"]:
        #         ui_doc += f"This element can be swiped directly without tapping. You can swipe horizontally on " \
        #                 f"this UI element. {doc_content['h_swipe']}\n\n"
        # # print_with_color(f"Documentations retrieved for the current interface:\n{ui_doc}", "magenta")
        # ui_doc = """
        # You also have access to the following documentations that describes the functionalities of UI 
        # elements you can interact on the screen. These docs are crucial for you to determine the target of your 
        # next action. You should always prioritize these documented elements for interaction:""" + ui_doc
        # print_with_color("Thinking about what to do in the next step...", "cyan")
        # prompt_action = prompts.task_template_action
        # prompt_action = re.sub(r"<ui_document>", ui_doc, prompt_action)
        # prompt_action = re.sub(r"<task_description>", task_desc, prompt_action)
        # prompt_action = re.sub(r"<like>", like, prompt_action)
        # status, rsp = mllm.get_model_response(prompt_action, [image])
        # res = parse_explore_rsp(rsp, new_video, 'action')
        # print(prompt_action)
        # print(rsp)
        # print(res)
        # prompt = prompt_understand + "\n=====\n" + like +":"+ reason + "\n=====\n" + prompt_action
        
        ## new action
        if like.lower() == 'like':
            action = 'tap'
        elif like.lower() == 'dislike':
            action = 'swipe'
        status = 1
        prompt = prompt_understand + "\n=====\n" + like +":"+ reason
    else:
        draw_bbox_multi(screenshot_path, os.path.join(task_dir, f"{dir_name}_{round_count}_action2_labeled.png"), elem_list,
                        dark_mode=configs["DARK_MODE"])
        image = os.path.join(task_dir, f"{dir_name}_{round_count}_action2_labeled.png")
        # ui_doc = ""
        # for i, elem in enumerate(elem_list):
        #     doc_path = os.path.join(docs_dir, f"{elem.uid}.txt")
        #     if not os.path.exists(doc_path):
        #         continue
        #     ui_doc += f"Documentation of UI element labeled with the numeric tag '{i + 1}':\n"
        #     doc_content = ast.literal_eval(open(doc_path, "r").read())
        #     if doc_content["tap"]:
        #         ui_doc += f"This UI element is clickable. {doc_content['tap']}\n\n"
        #     if doc_content["text"]:
        #         ui_doc += f"This UI element can receive text input. The text input is used for the following " \
        #                 f"purposes: {doc_content['text']}\n\n"
        #     if doc_content["long_press"]:
        #         ui_doc += f"This UI element is long clickable. {doc_content['long_press']}\n\n"
        #     if doc_content["v_swipe"]:
        #         ui_doc += f"This element can be swiped directly without tapping. You can swipe vertically on " \
        #                 f"this UI element. {doc_content['v_swipe']}\n\n"
        #     if doc_content["h_swipe"]:
        #         ui_doc += f"This element can be swiped directly without tapping. You can swipe horizontally on " \
        #                 f"this UI element. {doc_content['h_swipe']}\n\n"
        # # print_with_color(f"Documentations retrieved for the current interface:\n{ui_doc}", "magenta")
        # ui_doc = """
        # You also have access to the following documentations that describes the functionalities of UI 
        # elements you can interact on the screen. These docs are crucial for you to determine the target of your 
        # next action. You should always prioritize these documented elements for interaction:""" + ui_doc
        # prompt = re.sub(r"<ui_document>", ui_doc, prompts.task_oldvideo)
        # status, rsp = mllm.get_model_response(prompt, [image])
        # res = parse_explore_rsp(rsp, new_video, 'action')
        action = 'swipe'
        status = 1
        prompt = ''
    if status:
        with open(log_path, "a") as logfile:
            log_item = {"step": round_count, "prompt": prompt, "image": f"{dir_name}_{round_count}_labeled.png"}
                        # ,"response": rsp}
            logfile.write(json.dumps(log_item) + "\n")
        if new_video:
            with open(my_log_path, "a") as my_logfile:
                my_log_item = {"round": round_count, "time": int(time.time()), "xml": f"{dir_name}_{round_count}.xml", "viewing": viewing, "like":like, 'reason':reason}
                my_logfile.write(json.dumps(my_log_item) + "\n")
        if action == "tap":
            ret = controller.tap(xt, yt)
            if verbose:
                print_with_color("喜欢视频，点赞！\n", 'green')
            new_video = False
            if ret == "ERROR":
                print_with_color("ERROR: tap execution failed", "red")
                break
        elif action == "swipe":
            if verbose:
                if new_video:
                    print_with_color("不喜欢，上滑观看下一个视频！\n",'green')
                else:
                    print_with_color("已点赞，上滑观看下一个视频！\n",'green')
            ret = controller.swipe(xs, ys, 'up', 'long')
            new_video = True
            if ret == "ERROR":
                print_with_color("ERROR: swipe execution failed", "red")
                break
    else:
        print_with_color(rsp, "red")
        break

if task_complete:
    print_with_color("Task completed successfully", "green")
elif round_count == configs["MAX_ROUNDS"]:
    print_with_color("Task finished due to reaching max rounds", "green")
else:
    print_with_color("Task finished unexpectedly", "red")
