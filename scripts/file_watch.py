# @file file_watch.py
# @brief 利用watchdog包监控用户演示行为
# @author Zhuoxuan Xie
# @email 1206852606@qq.com
# @date 2024-06-15

from watchdog.events import FileSystemEventHandler
from utils import print_with_color
import time
import os

def keyboard_on_press(key, event_handler):
    # print('字母键{0} press'.format(key.char))
    if key.char == 'e':
        event_handler.end = 1
        return 0

# 参照watchdog包使用方法
class EventRecord_Handler(FileSystemEventHandler):

    def __init__(self, fname) -> None:
        super().__init__()
        self.fname = ".\\" + fname
        self.g_pid = -1
        self.ready = 0
        self.end = 0
        self.s_time = 0
        self.a_time = 0

    def __get_gepid(self, file_name):
        # print("jinrugetpid\n")
        while 1:
            with open(file_name, mode='r') as f:
                l = f.readlines()
                # print(len(l))
                if len(l) > 1:
                    return int(l[0])
                time.sleep(0.01)
                                  
    def on_created(self, event):
        if not event.is_directory and event.src_path == self.fname:
            # print(f'检测到文件 {event.src_path} 的创建\n')
            # os.system("cls")
            print_with_color(f"启动用时 {time.time()-eval(self.s_time)} 秒", 'cyan')
            print_with_color("请开始第 1 步演示, 每次演示只可以选择点赞或上滑中的一个，演示完成后请等待下次提示！", 'yellow')
            return 0
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path == self.fname and self.ready==0:
            # print(f'检测到文件 {event.src_path} 的修改\n')
            # time.sleep(0.3)
            self.g_pid = self.__get_gepid(event.src_path)
            # print(self.g_pid)
            while 1:
                self.a_time = time.time()
                count = 0
                last_line = ""
                with open(event.src_path, mode='r') as f:
                    for l in f.readlines():
                        if len(l)>0 and l[0:5]=='/dev/':
                            l = l.strip('\n').split()
                            # print(l)
                            if l[2] == 'ABS_MT_TRACKING_ID':
                                count = count + 1
                            elif l[2] == 'KEY_E':
                                return 0
                            last_line = l[3]
                if count == 2 and last_line=='00000000':
                    # print("文件写入一个动作完成！\n")
                    self.ready = 1
                    return 0
                # time.sleep(0.2)

