# @file run_like.py
# @brief 在假设一个用户不喜欢所有视频的场景下，进行行为模拟，测试及演示使用
# @author Zhuoxuan Xie
# @email 1206852606@qq.com
# @date 2024-06-15

import argparse
import os

from scripts.utils import print_with_color
import warnings

warnings.filterwarnings('ignore')
arg_desc = "AppAgent - deployment phase"
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=arg_desc)
parser.add_argument("--app")
parser.add_argument("--root_dir", default="./")
args = vars(parser.parse_args())

app = args["app"]
root_dir = args["root_dir"]

# print_with_color("Welcome to the deployment phase of AppAgent!\nBefore giving me the task, you should first tell me "
#                  "the name of the app you want me to operate and what documentation base you want me to use. I will "
#                  "try my best to complete the task without your intervention. First, please enter the main interface "
#                  "of the app on your phone and provide the following information.", "yellow")

if not app:
    # print_with_color("What is the name of the target app?", "blue")
    app = "blbl"
    # app = input()
    app = app.replace(" ", "")

os.system(f"python -W ignore scripts/task_dislike_executor.py --app {app} --root_dir {root_dir}")
