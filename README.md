# AppAgent_shortvideo
基于开源项目 [AppAgent](https://github.com/mnotgod96/AppAgent)，针对短视频推荐场景进行二次开发，AppAgent 的详细介绍请参考其官方说明。

## 基本功能概述
本项目主要分为行为学习、实际模拟两个模块。
+ 行为学习模块主要负责理解短视频App的基础操作逻辑，如点赞、上滑；
+ 实际模拟模块负责模拟真实用户与短视频APP进行交互，要根据所模拟用户的喜好对每个视频作出相应的操作

## 项目特色
+ 利用了多模态大模型强大的界面理解能力，可以做到在学习阶段不依赖固定屏幕坐标的指示，由大模型自行体会当前ui布局下所需学习的控件的作用；
+ 在实际模拟阶段，由于短视频推荐场景下动作空间的有限性，可以最大限度的避免误操作并对操作流程进行显著加速；

## 项目运行
### 1. 基础配置
1. 在电脑上下载并安装 [Android Debug Bridge](https://developer.android.com/tools/adb)(adb)，这是一个命令行工具，可让您从电脑与 Android 设备通信。
2. 获取安卓设备并启用 USB 调试，可在 "设置 "的 "开发人员选项 "中找到。
3. 使用 USB 电缆将设备连接到电脑。
4. (可选）如果您没有安卓设备, 我们建议您下载 [Android Studio](https://developer.android.com/studio/run/emulator) 并使用其自带的模拟器。模拟器可以在 Android Studio 的设备管理器中找到。您可以从互联网上下载 APK 文件并将其拖到模拟器上，从而在模拟器上安装应用程序。本项目可以检测模拟设备并在其上操作应用程序，就像操作真实设备一样。
5. 克隆此 repo 并安装依赖项。本项目中的所有脚本都是用 Python 3 编写的，因此请确保已安装。
```bash
cd AppAgent_ShortVideo
pip install -r requirements.txt
```
### 2. Agent配置
AppAgent_shortvideo 需要由一个多模式模型提供支持，该模型可以接收文本和视觉输入。在实验中，我们使用 'gpt-4-vision-preview' 作为模型，来决定如何采取行动完成智能手机上的任务。

要将请求配置为 GPT-4V，应修改根目录中的 config.yaml。要试用 AppAgent_shortvideo，必须配置两个关键参数：
1. OpenAI API 密钥：您必须从 OpenAI 购买合格的 API 密钥，才能访问 GPT-4V。
2. 请求间隔：这是连续 GPT-4V 请求之间的时间间隔（以秒为单位），用于控制向 GPT-4V 请求的频率。请根据账户状态调整该值。

您也可以尝试使用 qwen-vl-max (通义千问-VL) 作为替代多模式模型，为 AppAgent_shortvideo 提供动力。该模型目前可免费使用，但与 GPT-4V 相比，它在 AppAgent_shortvideo 中的性能较差。

要使用它，您需要创建一个阿里云账户，并创建一个 [Dashscope API](https://help.aliyun.com/zh/dashscope/developer-reference/acquisition-and-configuration-of-api-key?spm=a2c4g.11186623.0.i1) 密钥，将其填入 config.yaml 文件中的 DASHSCOPE_API_KEY 字段。同时将 MODEL 字段从 OpenAI 更改为 Qwen。

如果要使用自己的模型测试 AppAgent_shortvideo，则应相应地在 scripts/model.py 中编写一个新的模型类。

### 3. 行为学习阶段
此解决方案要求用户先演示类似的任务。AppAgent_shortvideo 将从演示中学习，并为演示过程中看到的用户界面元素生成文档。要开始人工演示，应在根目录下运行 learn.py。您需要根据提示进行下一步操作。当您认为演示结束时，请键入'e'来结束演示。
```bash
python learn.py
```
### 4. 实际模拟阶段
行为学习阶段结束后，可以在根目录下运行 run.py。按照提示输入应用程序名称，选择希望Agent使用的相应文档库，并提供任务描述。然后，Agent就会为您完成任务。
```bash
python run.py
```

## 工程结构说明

```angular2html
.
├── apps Agent总结的交互元素说明书文件存放地
├── scripts [重点]项目源代码存放地
│   ├── and_controller.py [核心代码]封装adb相关方法，实现控制手机点击、滑动等功能
│   ├── coldstart.py 项目第一次启动较慢，此文件进行一次简单的启动，加速下一次实际启动的过程
│   ├── config.py 读取配置文件
│   ├── document_generation.py [核心代码]负责生成交互元素说明书
│   ├── file_watch.py [核心代码]负责监控学习阶段用户的演示动作
│   ├── get_xy.py 负责持久化所需元素的坐标
│   ├── model.py 封装大模型调用过程
│   ├── my_prompts.py 存放项目所需的所有prompts
│   ├── self_explorer.py 学习阶段采用自我探索（废弃，准确率不符合目前需求）
│   ├── step_recorder.py [核心代码]记录学习阶段的每一步动作前后的UI界面
│   ├── task_executor.py [核心代码]负责组织实际模拟阶段的流程和所需函数
│   └── utils.py  工具函数
├── config.yaml  配置文件
├── learn.py 学习阶段入口文件：先进入step_recorder记录用户演示行为,再进入document_generation生成说明书
├── persona1.json 人设文件
├── replay.py 重现指定task目录的交互记录
└── run.py 实际模拟阶段入口文件：进入task_executor
```
