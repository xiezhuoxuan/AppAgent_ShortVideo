# @file replay.py
# @brief 回放指定的模拟交互记录
# @author Zhuoxuan Xie
# @email 1206852606@qq.com
# @date 2024-06-15

import argparse
import os
import time
from scripts.utils import print_with_color
import re
import cv2
import json

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--task_dir", default="./")
parser.add_argument("--app", default="blbl")
args = vars(parser.parse_args())
atask_dir = args['task_dir']
task_dir = os.path.join("./tasks", atask_dir)
# print(args['task_dir'][0])
# print(task_dir)
task_log = os.path.join(task_dir, f"mylog_{args['app']}_{atask_dir}.txt")
# print(task_log)
with open(task_log, 'r') as f:
    for l in f.readlines():
        content = json.loads(l)
        print_with_color(f"Round {content['round']}", "green")
        print_with_color("viewing:", "green")
        print_with_color(f"{content['viewing']}")
        print_with_color("Like:", "green")
        print_with_color(f"{content['like']}")
        print_with_color("reason:", "green")
        print_with_color(f"{content['reason']}") 

        round = content['round']
        islike = content['like'].lower()
        if islike == 'like':
            print_with_color("action:", 'green')
            print_with_color("喜欢并点赞") 
            image_path = atask_dir + f"_{round}_action2.png"    
        else:
            print_with_color("action:", 'green')
            print_with_color("不喜欢不点赞") 
            image_path = atask_dir + f"_{round}.png"
        image_path = os.path.join(task_dir, image_path)
        print(image_path)
        image = cv2.imread(image_path)
        cv2.namedWindow(f'Picture {round}',0)
        cv2.moveWindow(f"Picture {round}", 1190, 25)
        cv2.resizeWindow(f'Picture {round}', 324, 720)
        
        cv2.imshow(f'Picture {round}',image)
        cv2.waitKey(3000)   
        # time.sleep(2)
        cv2.destroyWindow(f'Picture {round}')
        # time.sleep(1)
