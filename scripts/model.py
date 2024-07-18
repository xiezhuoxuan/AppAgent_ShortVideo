import re
from abc import abstractmethod
from typing import List
from http import HTTPStatus

import requests
import dashscope

from utils import print_with_color, encode_image


class BaseModel:
    def __init__(self):
        pass

    @abstractmethod
    def get_model_response(self, prompt: str, images: List[str]) -> tuple[bool, str]:
        pass


class OpenAIModel(BaseModel):
    def __init__(self, base_url: str, api_key: str, model: str, temperature: float, max_tokens: int):
        super().__init__()
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def get_model_response(self, prompt: str, images: List[str]) -> tuple[bool, str]:
        content = [
            {
                "type": "text",
                "text": prompt
            }
        ]
        for img in images:
            base64_img = encode_image(img)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_img}"
                }
            })
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        response = requests.post(self.base_url, headers=headers, json=payload).json()
        if "error" not in response:
            usage = response["usage"]
            prompt_tokens = usage["prompt_tokens"]
            completion_tokens = usage["completion_tokens"]
            print_with_color(f"Request cost is "
                             f"${'{0:.2f}'.format(prompt_tokens / 1000 * 0.01 + completion_tokens / 1000 * 0.03)}",
                             "yellow")
        else:
            return False, response["error"]["message"]
        return True, response["choices"][0]["message"]["content"]


class QwenModel(BaseModel):
    def __init__(self, api_key: str, model: str):
        super().__init__()
        self.model = model
        dashscope.api_key = api_key

    def get_model_response(self, prompt: str, images: List[str]) -> tuple[bool, str]:
        # print("进入!\n")
        content = [{
            "text": prompt
        }]
        for img in images:
            img_path = f"file://{img}"
            content.append({
                "image": img_path
            })
        messages = [
            {
                "role": "user",
                "content": content
            }
        ]
        # print("call\n")
        response = dashscope.MultiModalConversation.call(model=self.model, messages=messages)
        # print("return\n")
        if response.status_code == HTTPStatus.OK:
            # print("xzx"*20)
            # print(response)
            return True, response.output.choices[0].message.content[0]["text"]
        else:
            return False, response.message

# 修改
# 解析大模型返回值
# rsp返回值，new_video是否是新视频, phase是哪个阶段（图文理解、喜好判断、操作）, p控制是否打印信息
def parse_explore_rsp(rsp, new_video, phase, p=1):
    try:
        if phase == 'understand':
            viewing = re.findall(r"Viewing:\s*(.*?)$", rsp, re.MULTILINE)[0]
            title = re.findall(r"Title:\s*(.*?)$", rsp, re.MULTILINE)[0]
            if new_video:
                print_with_color("Observation:", "yellow")
                print_with_color(viewing + f"\t And the title is {title}", "magenta")
                return [viewing, title]
        if phase == 'likeornot':
            like = re.findall(r"Like:\s*(.*?)$", rsp, re.MULTILINE)[0]
            reason = re.findall(r"Reason:\s*(.*?)$", rsp, re.MULTILINE)[0]
            if new_video:
                print_with_color("Like:", "yellow")
                print_with_color(like, "magenta")
                print_with_color("Reason:", "yellow")
                print_with_color(reason, "magenta")
                return [reason, like]
        if phase == 'action':
            think = re.findall(r"Thought:\s*(.*?)$", rsp, re.MULTILINE)[0]
            act = re.findall(r"Action:\s*(.*?)$", rsp, re.MULTILINE)[0]
            if p:    
                print_with_color("Thought:", "yellow")
                print_with_color(think, "magenta")
                print_with_color("Action:", "yellow")
                if act[0] == 's':
                    print_with_color("上滑", "magenta")
                elif act[0] == 't':
                    print_with_color("点赞", "magenta")
            if "FINISH" in act:
                return ["FINISH"]
            act_name = act.split("(")[0]
            if act_name == "tap":
                area = int(re.findall(r"tap\((.*?)\)", act)[0])
                return [act_name, area]
                # return [act_name, area, summary]
            elif act_name == "text":
                input_str = re.findall(r"text\((.*?)\)", act)[0][1:-1]
                return [act_name, input_str]
                # return [act_name, input_str, summary]
            elif act_name == "long_press":
                area = int(re.findall(r"long_press\((.*?)\)", act)[0])
                return [act_name, area]
                # return [act_name, area, summary]
            elif act_name == "swipe":
                params = re.findall(r"swipe\((.*?)\)", act)[0]
                area, swipe_dir, dist = params.split(",")
                area = int(area)
                swipe_dir = swipe_dir.strip()[1:-1]
                dist = dist.strip()[1:-1]
                return [act_name, area, swipe_dir, dist]
                # return [act_name, area, swipe_dir, dist, summary]
            elif act_name == "grid":
                return [act_name]
            else:
                print_with_color(f"ERROR: Undefined act {act_name}!", "red")
                return ["ERROR"]
    except Exception as e:
        print_with_color(f"ERROR: an exception occurs while parsing the model response: {e}", "red")
        print_with_color(rsp, "red")
        return ["ERROR"]


def parse_grid_rsp(rsp, new_video):
    try:
        observation = re.findall(r"Viewing: (.*?)$", rsp, re.MULTILINE)[0]
        title = re.findall(r"Title: (.*?)$", rsp, re.MULTILINE)[0]
        like = re.findall(r"Like: (.*?)$", rsp, re.MULTILINE)[0]
        reason = re.findall(r"Reason: (.*?)$", rsp, re.MULTILINE)[0]
        think = re.findall(r"Thought: (.*?)$", rsp, re.MULTILINE)[0]
        act = re.findall(r"Action: (.*?)$", rsp, re.MULTILINE)[0]
        # summary = re.findall(r"Summary: (.*?)$", rsp, re.MULTILINE)[0]
        if new_video:
            print_with_color("Observation:", "yellow")
            print_with_color(observation + f"\t And the title is {title}", "magenta")
            print_with_color("Like:", "yellow")
            print_with_color(like, "magenta")
            print_with_color("Reason:", "yellow")
            print_with_color(reason, "magenta")
        # print_with_color("Thought:", "yellow")
        # print_with_color(think, "magenta")
        print_with_color("Action:", "yellow")
        if act[0] == 's':
            print_with_color("上滑", "magenta")
        elif act[0] == 't':
            print_with_color("点赞", "magenta")
        # print_with_color("Summary:", "yellow")
        # print_with_color(summary, "magenta")
        if "FINISH" in act:
            return ["FINISH"]
        act_name = act.split("(")[0]
        if act_name == "tap":
            params = re.findall(r"tap\((.*?)\)", act)[0].split(",")
            area = int(params[0].strip())
            subarea = params[1].strip()[1:-1]
            return [act_name + "_grid", area, subarea]
            # return [act_name + "_grid", area, subarea, summary]
        elif act_name == "long_press":
            params = re.findall(r"long_press\((.*?)\)", act)[0].split(",")
            area = int(params[0].strip())
            subarea = params[1].strip()[1:-1]
            return [act_name + "_grid", area, subarea]
            # return [act_name + "_grid", area, subarea, summary]
        elif act_name == "swipe":
            params = re.findall(r"swipe\((.*?)\)", act)[0].split(",")
            start_area = int(params[0].strip())
            start_subarea = params[1].strip()[1:-1]
            end_area = int(params[2].strip())
            end_subarea = params[3].strip()[1:-1]
            return [act_name + "_grid", start_area, start_subarea, end_area, end_subarea]
            # return [act_name + "_grid", start_area, start_subarea, end_area, end_subarea, summary]
        elif act_name == "grid":
            return [act_name]
        else:
            print_with_color(f"ERROR: Undefined act {act_name}!", "red")
            return ["ERROR"]
    except Exception as e:
        print_with_color(f"ERROR: an exception occurs while parsing the model response: {e}", "red")
        print_with_color(rsp, "red")
        return ["ERROR"]

# 解析大模型返回值    new_video代表这个视频操作过没，新旧视频有不同处理逻辑
# 新视频判断是否喜欢然后标记为老视频，老视频直接划走
def my_parse_explore_rsp(rsp, new_video):
    try:
        observation = re.findall(r"Viewing: (.*?)$", rsp, re.MULTILINE)[0]
        # print("xzx000"*20)
        title = re.findall(r"Title: (.*?)$", rsp, re.MULTILINE)[0]
        think = re.findall(r"Thought: (.*?)$", rsp, re.MULTILINE)[0]
        act = re.findall(r"Action: (.*?)$", rsp, re.MULTILINE)[0]
        # summary = re.findall(r"Summary: (.*?)$", rsp, re.MULTILINE)[0]
        if new_video:
            print_with_color("Observation:", "yellow")
            print_with_color(observation + f"\t And the title is {title}", "magenta")
            # print_with_color("Title:", "yellow")
            # print_with_color(title, "magenta")
        # print_with_color("Thought:", "yellow")
        # print_with_color(think, "magenta")
        # print_with_color("Action:", "yellow")
        # print_with_color(act, "magenta")
        print_with_color("Action:", "yellow")
        if act[0] == 's':
            print_with_color("上滑", "magenta")
        elif act[0] == 't':
            print_with_color("点赞", "magenta")
        # print_with_color("Summary:", "yellow")
        # print_with_color(summary, "magenta")
        if "FINISH" in act:
            return ["FINISH"]
        act_name = act.split("(")[0]
        if act_name == "tap":
            area = int(re.findall(r"tap\((.*?)\)", act)[0])
            return [act_name, area]
            # return [act_name, area, summary]
        elif act_name == "text":
            input_str = re.findall(r"text\((.*?)\)", act)[0][1:-1]
            return [act_name, input_str]
            # return [act_name, input_str, summary]
        elif act_name == "long_press":
            area = int(re.findall(r"long_press\((.*?)\)", act)[0])
            return [act_name, area]
            # return [act_name, area, summary]
        elif act_name == "swipe":
            params = re.findall(r"swipe\((.*?)\)", act)[0]
            area, swipe_dir, dist = params.split(",")
            area = int(area)
            swipe_dir = swipe_dir.strip()[1:-1]
            dist = dist.strip()[1:-1]
            return [act_name, area, swipe_dir, dist]
            # return [act_name, area, swipe_dir, dist, summary]
        elif act_name == "grid":
            return [act_name]
        else:
            print_with_color(f"ERROR: Undefined act {act_name}!", "red")
            return ["ERROR"]
    except Exception as e:
        print_with_color(f"ERROR: an exception occurs while parsing the model response: {e}", "red")
        print_with_color(rsp, "red")
        return ["ERROR"]

# 解析大模型返回值    new_video代表这个视频操作过没，新旧视频有不同处理逻辑
# 主要是应对大模型作出了自己的自由动作（我们意料之外的），其实用不到
def my_parse_grid_rsp(rsp, new_video):
    try:
        observation = re.findall(r"Viewing: (.*?)$", rsp, re.MULTILINE)[0]
        title = re.findall(r"Title: (.*?)$", rsp, re.MULTILINE)[0]
        think = re.findall(r"Thought: (.*?)$", rsp, re.MULTILINE)[0]
        act = re.findall(r"Action: (.*?)$", rsp, re.MULTILINE)[0]
        # summary = re.findall(r"Summary: (.*?)$", rsp, re.MULTILINE)[0]
        if new_video:
            print_with_color("Observation:", "yellow")
            print_with_color(observation + f"\t And the title is {title}", "magenta")
        # print_with_color("Thought:", "yellow")
        # print_with_color(think, "magenta")
        print_with_color("Action:", "yellow")
        if act[0] == 's':
            print_with_color("上滑", "magenta")
        elif act[0] == 't':
            print_with_color("点赞", "magenta")
        # print_with_color("Summary:", "yellow")
        # print_with_color(summary, "magenta")
        if "FINISH" in act:
            return ["FINISH"]
        act_name = act.split("(")[0]
        if act_name == "tap":
            params = re.findall(r"tap\((.*?)\)", act)[0].split(",")
            area = int(params[0].strip())
            subarea = params[1].strip()[1:-1]
            return [act_name + "_grid", area, subarea]
            # return [act_name + "_grid", area, subarea, summary]
        elif act_name == "long_press":
            params = re.findall(r"long_press\((.*?)\)", act)[0].split(",")
            area = int(params[0].strip())
            subarea = params[1].strip()[1:-1]
            return [act_name + "_grid", area, subarea]
            # return [act_name + "_grid", area, subarea, summary]
        elif act_name == "swipe":
            params = re.findall(r"swipe\((.*?)\)", act)[0].split(",")
            start_area = int(params[0].strip())
            start_subarea = params[1].strip()[1:-1]
            end_area = int(params[2].strip())
            end_subarea = params[3].strip()[1:-1]
            return [act_name + "_grid", start_area, start_subarea, end_area, end_subarea]
            # return [act_name + "_grid", start_area, start_subarea, end_area, end_subarea, summary]
        elif act_name == "grid":
            return [act_name]
        else:
            print_with_color(f"ERROR: Undefined act {act_name}!", "red")
            return ["ERROR"]
    except Exception as e:
        print_with_color(f"ERROR: an exception occurs while parsing the model response: {e}", "red")
        print_with_color(rsp, "red")
        return ["ERROR"]


def parse_reflect_rsp(rsp):
    try:
        decision = re.findall(r"Decision: (.*?)$", rsp, re.MULTILINE)[0]
        think = re.findall(r"Thought: (.*?)$", rsp, re.MULTILINE)[0]
        print_with_color("Decision:", "yellow")
        print_with_color(decision, "magenta")
        print_with_color("Thought:", "yellow")
        print_with_color(think, "magenta")
        if decision == "INEFFECTIVE":
            return [decision, think]
        elif decision == "BACK" or decision == "CONTINUE" or decision == "SUCCESS":
            doc = re.findall(r"Documentation: (.*?)$", rsp, re.MULTILINE)[0]
            print_with_color("Documentation:", "yellow")
            print_with_color(doc, "magenta")
            return [decision, think, doc]
        else:
            print_with_color(f"ERROR: Undefined decision {decision}!", "red")
            return ["ERROR"]
    except Exception as e:
        print_with_color(f"ERROR: an exception occurs while parsing the model response: {e}", "red")
        print_with_color(rsp, "red")
        return ["ERROR"]
