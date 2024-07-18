# @file my_prompts.py
# @brief 存放项目所需的所有prompts
# @author Zhuoxuan Xie
# @email 1206852606@qq.com
# @date 2024-06-15

tap_doc_template = """I will give you the screenshot of a mobile app before and after tapping the UI element labeled 
with the number <ui_element> on the screen. The numeric tag of each element is located at the center of the element. 
Tapping this UI element is a necessary part of proceeding with a larger task, which is to <task_desc>. Your task is to 
describe the functionality of the UI element concisely in one or two sentences. Notice that your description of the UI 
element should focus on the general function. For example, if the UI element is used to navigate to the chat window 
with John, your description should not include the name of the specific person. Just say: "Tapping this area will 
navigate the user to the chat window". Never include the numeric tag of the UI element in your description. You can use 
pronouns such as "the UI element" to refer to the element."""

text_doc_template = """I will give you the screenshot of a mobile app before and after typing in the input area labeled
with the number <ui_element> on the screen. The numeric tag of each element is located at the center of the element. 
Typing in this UI element is a necessary part of proceeding with a larger task, which is to <task_desc>. Your task is 
to describe the functionality of the UI element concisely in one or two sentences. Notice that your description of the 
UI element should focus on the general function. For example, if the change of the screenshot shows that the user typed 
"How are you?" in the chat box, you do not need to mention the actual text. Just say: "This input area is used for the 
user to type a message to send to the chat window.". Never include the numeric tag of the UI element in your 
description. You can use pronouns such as "the UI element" to refer to the element."""

long_press_doc_template = """I will give you the screenshot of a mobile app before and after long pressing the UI 
element labeled with the number <ui_element> on the screen. The numeric tag of each element is located at the center of 
the element. Long pressing this UI element is a necessary part of proceeding with a larger task, which is to 
<task_desc>. Your task is to describe the functionality of the UI element concisely in one or two sentences. Notice 
that your description of the UI element should focus on the general function. For example, if long pressing the UI 
element redirects the user to the chat window with John, your description should not include the name of the specific 
person. Just say: "Long pressing this area will redirect the user to the chat window". Never include the numeric tag of 
the UI element in your description. You can use pronouns such as "the UI element" to refer to the element."""

swipe_doc_template = """I will give you the screenshot of a mobile app before and after swiping <swipe_dir> the UI 
element labeled with the number <ui_element> on the screen. The numeric tag of each element is located at the center of 
the element. Swiping this UI element is a necessary part of proceeding with a larger task, which is to <task_desc>. 
Your task is to describe the functionality of the UI element concisely in one or two sentences. Notice that your 
description of the UI element should be as general as possible. For example, if swiping the UI element increases the 
contrast ratio of an image of a building, your description should be just like this: "Swiping this area enables the 
user to tune a specific parameter of the image". Never include the numeric tag of the UI element in your description. 
You can use pronouns such as "the UI element" to refer to the element."""

refine_doc_suffix = """\nA documentation of this UI element generated from previous demos is shown below. Your 
generated description should be based on this previous doc and optimize it. Notice that it is possible that your 
understanding of the function of the UI element derived from the given screenshots conflicts with the previous doc, 
because the function of a UI element can be flexible. In this case, your generated description should combine both.
Old documentation of this UI element: <old_doc>"""

task_template_understand = """You are an agent that is trained to perform some basic tasks on a smartphone. You will be given a 
smartphone screenshot. The interactive UI elements on the screenshot are labeled with numeric tags starting from 1. The 
numeric tag of each interactive element is located in the center of the element.

Now, given the documentation and the following labeled screenshot. Your output should include two parts in the given format:
Viewing: <Describe what you observe in the image using english. Do not include the numeric tag in your viewing>
Title: <This is a screenshot of a short video. Please determine which text in the picture is the title of the video. Please ensure that the title consists of Chinese characters and does not include the publisher's username or button names such as "关注" "点赞" "发弹幕," etc. Output the title in english.>
"""

task_template_likeornot = """You are an agent that is trained to perform some basic tasks on a smartphone. You will be given a 
smartphone screenshot. The interactive UI elements on the screenshot are labeled with numeric tags starting from 1. The 
numeric tag of each interactive element is located in the center of the element.

Now, given the following labeled screenshot. The screenshot's description is <viewing>, title is <title>.
Your output should include two parts in the given format:
Reason: <Please share your rationale behind whether you enjoyed or did not enjoy this video, elaborating on the specific elements that influenced your preference.>
Like: <You are role-playing as a short video viewer with specific preferences outlined as "<user_description>". Please respond whether you like your viewing or not. Your response must include either "like" or "dislike" and must not include other content.>
"""

task_template_action = """You are an agent that is trained to perform some basic tasks on a smartphone. You will be given a 
smartphone screenshot. The interactive UI elements on the screenshot are labeled with numeric tags starting from 1. The 
numeric tag of each interactive element is located in the center of the element.

You can call the following functions to control the smartphone:

1. tap(element: int)
This function is used to tap an UI element shown on the smartphone screen.
"element" is a numeric tag assigned to an UI element shown on the smartphone screen.
A simple use case can be tap(5), which taps the UI element labeled with the number 5.

2. swipe(element: int, direction: str, dist: str)
This function is used to swipe an UI element shown on the smartphone screen, usually a scroll view or a slide bar.
"element" is a numeric tag assigned to an UI element shown on the smartphone screen. "direction" is a string that 
represents one of the four directions: up, down, left, right. "direction" must be wrapped with double quotation 
marks. "dist" determines the distance of the swipe and can be one of the three options: short, medium, long. You should 
choose the appropriate distance option according to your need.
A simple use case can be swipe(21, "up", "medium"), which swipes up the UI element labeled with the number 21 for a 
medium distance.

3. grid()
You should call this function when you find the element you want to interact with is not labeled with a numeric tag and 
other elements with numeric tags cannot help with the task. The function will bring up a grid overlay to divide the 
smartphone screen into small areas and this will give you more freedom to choose any part of the screen to tap, long 
press, or swipe.
<ui_document>
The task you need to complete is to <task_description>. And you <like> current video.
Now, given the documentation and the following labeled screenshot, you need to think and call the function needed to 
proceed with the task. Your output should include two parts in the given format:
Thought: <To complete the given task, what is the next step I should do.>
Action: <The function call with the correct parameters to proceed with the task. If you believe the task is completed or 
there is nothing to be done, you should output FINISH. You cannot output anything else except a function call or FINISH 
in this field.>
"""

task_template_grid = """You are an agent that is trained to perform some basic tasks on a smartphone. You will be given 
a smartphone screenshot overlaid by a grid. The grid divides the screenshot into small square areas. Each area is 
labeled with an integer in the top-left corner.

You can call the following functions to control the smartphone:

1. tap(area: int, subarea: str)
This function is used to tap a grid area shown on the smartphone screen. "area" is the integer label assigned to a grid 
area shown on the smartphone screen. "subarea" is a string representing the exact location to tap within the grid area. 
It can take one of the nine values: center, top-left, top, top-right, left, right, bottom-left, bottom, and 
bottom-right.
A simple use case can be tap(5, "center"), which taps the exact center of the grid area labeled with the number 5.

2. swipe(start_area: int, start_subarea: str, end_area: int, end_subarea: str)
This function is used to perform a swipe action on the smartphone screen, especially when you want to interact with a 
scroll view or a slide bar. "start_area" is the integer label assigned to the grid area which marks the starting 
location of the swipe. "start_subarea" is a string representing the exact location to begin the swipe within the grid 
area. "end_area" is the integer label assigned to the grid area which marks the ending location of the swipe. 
"end_subarea" is a string representing the exact location to end the swipe within the grid area.
The two subarea parameters can take one of the nine values: center, top-left, top, top-right, left, right, bottom-left, 
bottom, and bottom-right.
A simple use case can be swipe(21, "center", 25, "right"), which performs a swipe starting from the center of grid area 
21 to the right part of grid area 25.

The task you need to complete is to <task_description>.
Now, given the following labeled screenshot, you need to think and call the function needed to proceed with the task. 
Your output should include six parts in the given format:
Viewing : <Describe what you observe in the image. Do not include the numeric tag in your viewing>
Title: <This is a screenshot of a short video. Please determine which text in the picture is the title of the video. Please ensure that the title consists of Chinese characters and does not include the publisher's username or button names such as "关注" "点赞" "发弹幕," etc.>
Like: <You are role-playing as a short video viewer with specific preferences outlined as "<user_description>". Please respond whether you like your viewing or not. Your response must include either "like" or "dislike.">
Reason:<Please share your rationale behind whether you enjoyed or did not enjoy this video, elaborating on the specific elements that influenced your preference.>
Thought: <To complete the given task, what is the next step I should do.>
Action: <The function call with the correct parameters to proceed with the task. If you believe the task is completed or 
there is nothing to be done, you should output FINISH. You cannot output anything else except a function call or FINISH 
in this field.>
You can only take one action at a time, so please directly call the function."""

task_oldvideo = """You are an agent that is trained to perform some basic tasks on a smartphone. You will be given a 
smartphone screenshot. The interactive UI elements on the screenshot are labeled with numeric tags starting from 1. The 
numeric tag of each interactive element is located in the center of the element.

You can call the following functions to control the smartphone:

1. tap(element: int)
This function is used to tap an UI element shown on the smartphone screen.
"element" is a numeric tag assigned to an UI element shown on the smartphone screen.
A simple use case can be tap(5), which taps the UI element labeled with the number 5.

2. swipe(element: int, direction: str, dist: str)
This function is used to swipe an UI element shown on the smartphone screen, usually a scroll view or a slide bar.
"element" is a numeric tag assigned to an UI element shown on the smartphone screen. "direction" is a string that 
represents one of the four directions: up, down, left, right. "direction" must be wrapped with double quotation 
marks. "dist" determines the distance of the swipe and can be one of the three options: short, medium, long. You should 
choose the appropriate distance option according to your need.
A simple use case can be swipe(21, "up", "medium"), which swipes up the UI element labeled with the number 21 for a 
medium distance.

3. grid()
You should call this function when you find the element you want to interact with is not labeled with a numeric tag and 
other elements with numeric tags cannot help with the task. The function will bring up a grid overlay to divide the 
smartphone screen into small areas and this will give you more freedom to choose any part of the screen to tap, long 
press, or swipe.
<ui_document>
The task you need to complete is to <task_description>. 
Now, given the documentation and the following labeled screenshot, 
and you have liked the current video, you need to think and call the function needed to proceed to the next video.
Your output should include five parts in the given format:
Viewing: <Please output "This is not a new video.">
Title: <Please output "This is not a new video.">
Like: <Please output "This is not a new video.">
Reason: <Please output "This is not a new video.">
Thought: <To complete the given task, what is the next step I should do.>
Action: <The function call with the correct parameters to proceed with the task. If you believe the task is completed or 
there is nothing to be done, you should output FINISH. You cannot output anything else except a function call or FINISH 
in this field.>
"""

task_oldvideo_grid = """You are an agent that is trained to perform some basic tasks on a smartphone. You will be given 
a smartphone screenshot overlaid by a grid. The grid divides the screenshot into small square areas. Each area is 
labeled with an integer in the top-left corner.

You can call the following functions to control the smartphone:

1. tap(area: int, subarea: str)
This function is used to tap a grid area shown on the smartphone screen. "area" is the integer label assigned to a grid 
area shown on the smartphone screen. "subarea" is a string representing the exact location to tap within the grid area. 
It can take one of the nine values: center, top-left, top, top-right, left, right, bottom-left, bottom, and 
bottom-right.
A simple use case can be tap(5, "center"), which taps the exact center of the grid area labeled with the number 5.

2. swipe(start_area: int, start_subarea: str, end_area: int, end_subarea: str)
This function is used to perform a swipe action on the smartphone screen, especially when you want to interact with a 
scroll view or a slide bar. "start_area" is the integer label assigned to the grid area which marks the starting 
location of the swipe. "start_subarea" is a string representing the exact location to begin the swipe within the grid 
area. "end_area" is the integer label assigned to the grid area which marks the ending location of the swipe. 
"end_subarea" is a string representing the exact location to end the swipe within the grid area.
The two subarea parameters can take one of the nine values: center, top-left, top, top-right, left, right, bottom-left, 
bottom, and bottom-right.
A simple use case can be swipe(21, "center", 25, "right"), which performs a swipe starting from the center of grid area 
21 to the right part of grid area 25.

The task you need to complete is to <task_description>. 
Now, given the documentation and the following labeled screenshot, 
and you have liked the current video, you need to think and call the function needed to proceed to the next video.
Your output should include five parts in the given format:
Viewing: <Please output "This is not a new video.">
Title: <Please output "This is not a new video.">
Like: <Please output "This is not a new video.">
Reason: <Please output "This is not a new video.">
Thought: <To complete the given task, what is the next step I should do.>
Action: <The function call with the correct parameters to proceed with the task. If you believe the task is completed or 
there is nothing to be done, you should output FINISH. You cannot output anything else except a function call or FINISH 
in this field.>
"""