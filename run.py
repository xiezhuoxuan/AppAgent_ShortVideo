import argparse
import os
import time
from scripts.utils import print_with_color
import warnings
import sys

s_time = time.time()
warnings.filterwarnings('ignore')
arg_desc = "AppAgent - deployment phase"
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=arg_desc)
parser.add_argument("--app")
parser.add_argument("--root_dir", default="./")
parser.add_argument("--user_desc", default="persona1.json")

args = vars(parser.parse_args())
app = args["app"]
root_dir = args["root_dir"]
user_desc = args["user_desc"]
# print_with_color("Welcome to the deployment phase of AppAgent!\nBefore giving me the task, you should first tell me "
#                  "the name of the app you want me to operate and what documentation base you want me to use. I will "
#                  "try my best to complete the task without your intervention. First, please enter the main interface "
#                  "of the app on your phone and provide the following information.", "yellow")

if not app:
    # print_with_color("What is the name of the target app?", "blue")
    app = "blbl"
    # app = input()
    app = app.replace(" ", "")

os.system(f"python -W ignore scripts/task_executor.py --app {app} --root_dir {root_dir} --user_desc {user_desc} --s_time {s_time}")
