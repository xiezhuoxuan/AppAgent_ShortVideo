import os
import re
import subprocess
import xml.etree.ElementTree as ET
import uiautomator2 as u2
import chardet
import codecs
import time

from config import load_config
from utils import print_with_color


configs = load_config("./config.yaml")

class AndroidElement:
    def __init__(self, uid, bbox, attrib):
        self.uid = uid
        self.bbox = bbox
        self.attrib = attrib

def execute_adb(adb_command, p=1 ,t=0):
    # print(adb_command)
    result = subprocess.run(adb_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if t:
        time.sleep(t)
    if result.returncode == 0:
        return result.stdout.strip()
    if p:
        print_with_color(f"Command execution failed: {adb_command}", "red")
        print_with_color(result.stderr, "red")
    return "ERROR"

def execute_adb_nowait(adb_command, t=0):
    # print(adb_command)
    result = subprocess.Popen(adb_command, shell=True, stdout=subprocess.PIPE)
    if t:
        time.sleep(t)
    return result

# 获得像素坐标和event体系坐标的转换倍率
def get_eventwh_rate(w, h, ewh_size='event_weight_height.txt'):
    # 获取event体系高宽
    adb_command = f'adb shell getevent -p | grep -e "0035" -e "0036" >{ewh_size}'
    result = execute_adb(adb_command)
    ew, eh = -1, -1
    with open(ewh_size, mode='r') as f:
        for l in f.readlines():
            if len(l)>0:
                l = l.strip('\n').split(',')
                # print(l)
                if l[0].split()[0] == '0035' and ew == -1:
                    ew = int(l[2][4:])
                if l[0].split()[0] == '0036' and eh == -1:
                    eh = int(l[2][4:])
            if ew != -1 and eh != -1:
                break        
    rw = w / ew
    rh = h / eh
    return rw, rh

# 判断给定坐标是哪个元素的
def get_label_id(x, y, elem_list):
    for count, e in enumerate(elem_list):
        b = e.bbox
        if x >= b[0][0] and x <= b[1][0] and y >= b[0][1] and y <= b[1][1]:
            return count+1
    print_with_color("从坐标映射id失败！\n", "red")
    return -1

# 把adb监控到的操作翻译给大模型需要的格式
def autotrans(adb_event_path, elem_list, rw, rh):
    x_list = []
    y_list = []
    with open(adb_event_path, mode='r') as f:
        for l in f.readlines():
            if len(l)>0 and l[0:5]=='/dev/':
                l = l.strip('\n').split()
                # print(l)
                if l[2] == 'ABS_MT_POSITION_X':
                    x_list.append(l[3])
                elif l[2] == 'ABS_MT_POSITION_Y':
                    y_list.append(l[3])
    # print(x_list)
    # print(y_list)
    real_x = int(x_list[0], 16) * rw
    real_y = int(y_list[0], 16) * rh
    real_x1 = int(x_list[-1],16) * rw
    real_y1 = int(y_list[-1],16) * rh
    id = get_label_id(real_x, real_y, elem_list)
    if len(x_list) == 1 and len(y_list) == 1:
        action = 'tap'
    else:
        action = 'swipe'
    return action, id, [real_x,real_y,real_x1,real_y1]

def get_adb_event(f_name="envent_record.txt"):
    adb_command = f'adb shell "nohup getevent -l 2>&1 & echo $!" >{f_name}'
    p = execute_adb_nowait(adb_command, 0.2)
    g_pid = -1
    while 1:
        with open(f_name, mode='r') as f:
            l = f.readlines()
            if len(l) > 1:
                g_pid=int(l[0])
                break
    # print(g_pid)            
    command = f"adb shell kill -9 {g_pid}"
    command2 = f"adb shell ps | grep -w {g_pid} >kill_getevent.txt"
    user_input = "xxx"
    print("请开始演示，随时输入s结束演示！  输入end表示整个流程结束！\n")
    while user_input.lower() != "s" and user_input.lower() != "end":
        user_input = input()
    if user_input.lower() == "s":
        print("单步演示结束！\n")
        result = execute_adb(command)
        while 1:
            result2 = subprocess.run(command2, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if os.stat("kill_getevent.txt").st_size == 0:
                break
            time.sleep(0.1)
        p.kill()
        return f_name, 1
    elif user_input.lower() == "end":
        print("整个流程结束！\n")
        result = execute_adb(command)
        while 1:
            result2 = subprocess.run(command2, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if os.stat("kill_getevent.txt").st_size == 0:
                break
            time.sleep(0.1)
        p.kill()
        return f_name, 0
    result = execute_adb(command)
    p.kill()
    return f_name, -1

def list_all_devices():
    adb_command = "adb devices"
    device_list = []
    result = execute_adb(adb_command)
    if result != "ERROR":
        devices = result.split("\n")[1:]
        for d in devices:
            device_list.append(d.split()[0])

    return device_list


def get_id_from_element(elem):
    bounds = elem.attrib["bounds"][1:-1].split("][")
    x1, y1 = map(int, bounds[0].split(","))
    x2, y2 = map(int, bounds[1].split(","))
    elem_w, elem_h = x2 - x1, y2 - y1
    if "resource-id" in elem.attrib and elem.attrib["resource-id"]:
        elem_id = elem.attrib["resource-id"].replace(":", ".").replace("/", "_")
    else:
        elem_id = f"{elem.attrib['class']}_{elem_w}_{elem_h}"
    if "content-desc" in elem.attrib and elem.attrib["content-desc"] and len(elem.attrib["content-desc"]) < 20:
        content_desc = elem.attrib['content-desc'].replace("/", "_").replace(" ", "").replace(":", "_")
        elem_id += f"_{content_desc}"
    return elem_id


def traverse_tree(xml_path, elem_list, attrib, add_index=False):
    path = []
    for event, elem in ET.iterparse(xml_path, ['start', 'end']):
        if event == 'start':
            path.append(elem)
            if attrib in elem.attrib and elem.attrib[attrib] == "true":
                parent_prefix = ""
                if len(path) > 1:
                    parent_prefix = get_id_from_element(path[-2])
                bounds = elem.attrib["bounds"][1:-1].split("][")
                x1, y1 = map(int, bounds[0].split(","))
                x2, y2 = map(int, bounds[1].split(","))
                center = (x1 + x2) // 2, (y1 + y2) // 2
                elem_id = get_id_from_element(elem)
                if parent_prefix:
                    elem_id = parent_prefix + "_" + elem_id
                if add_index:
                    elem_id += f"_{elem.attrib['index']}"
                close = False
                for e in elem_list:
                    bbox = e.bbox
                    center_ = (bbox[0][0] + bbox[1][0]) // 2, (bbox[0][1] + bbox[1][1]) // 2
                    dist = (abs(center[0] - center_[0]) ** 2 + abs(center[1] - center_[1]) ** 2) ** 0.5
                    if dist <= configs["MIN_DIST"]:
                        close = True
                        break
                if not close:
                    elem_list.append(AndroidElement(elem_id, ((x1, y1), (x2, y2)), attrib))

        if event == 'end':
            path.pop()

def detect_file_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read()
    return chardet.detect(raw_data)['encoding']

class AndroidController:
    def __init__(self, device):
        self.device = device
        # 为了获取动态页面的xml布局文件
        self.d = u2.connect_usb(device)
        self.screenshot_dir = configs["ANDROID_SCREENSHOT_DIR"]
        self.xml_dir = configs["ANDROID_XML_DIR"]
        self.width, self.height = self.get_device_size()
        self.backslash = "\\"

    def get_device_size(self):
        adb_command = f"adb -s {self.device} shell wm size"
        result = execute_adb(adb_command)
        if result != "ERROR":
            return map(int, result.split(": ")[1].split("x"))
        return 0, 0

    def get_screenshot(self, prefix, save_dir):
        cap_command = f"adb -s {self.device} shell screencap -p " \
                      f"{os.path.join(self.screenshot_dir, prefix + '.png').replace(self.backslash, '/')}"
        pull_command = f"adb -s {self.device} pull " \
                       f"{os.path.join(self.screenshot_dir, prefix + '.png').replace(self.backslash, '/')} " \
                       f"{os.path.join(save_dir, prefix + '.png')}"
        result = execute_adb(cap_command)
        if result != "ERROR":
            result = execute_adb(pull_command)
            if result != "ERROR":
                return os.path.join(save_dir, prefix + ".png")
            return result
        return result

    # def get_xml(self, prefix, save_dir):
    #     dump_command = f"adb -s {self.device} shell uiautomator dump " \
    #                    f"{os.path.join(self.xml_dir, prefix + '.xml').replace(self.backslash, '/')}"
    #     pull_command = f"adb -s {self.device} pull " \
    #                    f"{os.path.join(self.xml_dir, prefix + '.xml').replace(self.backslash, '/')} " \
    #                    f"{os.path.join(save_dir, prefix + '.xml')}"
    #     result = execute_adb(dump_command)
    #     if result != "ERROR":
    #         result = execute_adb(pull_command)
    #         if result != "ERROR":
    #             return os.path.join(save_dir, prefix + ".xml")
    #         return result
    #     return result

    def get_xml(self, prefix, save_dir):
        xml = self.d.dump_hierarchy()        
        xml_path = os.path.join(save_dir, prefix + '.xml')
        target_encoding = 'UTF-8'
        with codecs.open(xml_path, 'w', target_encoding) as f:
            f.write(xml)
        return xml_path, None
        # with open(xml_path, 'w+') as f:
        #     f.write(xml)
        # # 定义源编码和目标编码
        # s_encoding = detect_file_encoding(xml_path)
        # if s_encoding == "GB2312":
        #     encoding = "GBK"
        # else:
        #     encoding = s_encoding
        # target_encoding = 'UTF-8'
        # # 读取原文件内容
        # with open(xml_path, 'r', encoding=encoding) as f:
        #     content = f.read()
        # # 写入新编码的文件
        # with codecs.open(xml_path, 'w', target_encoding) as f:
        #     f.write(content)
        # return xml_path, s_encoding

    def back(self):
        adb_command = f"adb -s {self.device} shell input keyevent KEYCODE_BACK"
        ret = execute_adb(adb_command)
        return ret

    def tap(self, x, y):
        adb_command = f"adb -s {self.device} shell input tap {x} {y}"
        ret = execute_adb(adb_command)
        return ret

    def text(self, input_str):
        input_str = input_str.replace(" ", "%s")
        input_str = input_str.replace("'", "")
        adb_command = f"adb -s {self.device} shell input text {input_str}"
        ret = execute_adb(adb_command)
        return ret

    def long_press(self, x, y, duration=1000):
        adb_command = f"adb -s {self.device} shell input swipe {x} {y} {x} {y} {duration}"
        ret = execute_adb(adb_command)
        return ret

    def swipe(self, x, y, direction, dist="medium", quick=False):
        unit_dist = int(self.width / 10)
        if dist == "long":
            unit_dist *= 3
        elif dist == "medium":
            unit_dist *= 2
        if direction == "up":
            offset = 0, -2 * unit_dist
        elif direction == "down":
            offset = 0, 2 * unit_dist
        elif direction == "left":
            offset = -1 * unit_dist, 0
        elif direction == "right":
            offset = unit_dist, 0
        else:
            return "ERROR"
        duration = 100 if quick else 400
        adb_command = f"adb -s {self.device} shell input swipe {x} {y} {x+offset[0]} {y+offset[1]} {duration}"
        ret = execute_adb(adb_command)
        return ret

    def swipe_precise(self, start, end, duration=400):
        start_x, start_y = start
        end_x, end_y = end
        adb_command = f"adb -s {self.device} shell input swipe {start_x} {start_x} {end_x} {end_y} {duration}"
        ret = execute_adb(adb_command)
        return ret
