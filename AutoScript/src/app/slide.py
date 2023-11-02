"""
!Deprecated
"""

import base64
from urllib.parse import parse_qs
from io import BytesIO
from pathlib import Path

import cv2
from cv2.typing import MatLike
import numpy as np
# from flask import Flask, request
from pydantic import BaseModel
from PIL import Image


# bg = "./py/images/gap.png"
# block = "./py/images/block.png"
def get_distance(tp: MatLike, bg: MatLike, im_show=False):
    """
    :param bg: 背景图路径或Path对象或图片二进制
        eg: 'assets/bg.jpg'
            Path('assets/bg.jpg')
    :param tp: 缺口图路径或Path对象或图片二进制
        eg: 'assets/tp.jpg'
            Path('assets/tp.jpg')
    :param im_show: 是否显示结果, <type 'bool'>; default: False
    :param save_path: 保存路径, <type 'str'/'Path'>; default: None
    :return: 缺口位置
    """
    # 边缘检测
    tp_gray = cv2.Canny(cv2.cvtColor(tp, cv2.COLOR_BGR2GRAY), 255, 255)
    bg_gray = cv2.Canny(cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY), 255, 255)
    # 目标匹配
    result = cv2.matchTemplate(bg_gray, tp_gray, cv2.TM_CCOEFF_NORMED)

    # 解析匹配结果
    # min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    *_, max_loc = cv2.minMaxLoc(result)

    distance = max_loc[0]
    # 需要绘制的方框高度和宽度
    tp_height, tp_width = tp_gray.shape[:2]
    # 矩形左上角点位置
    x, y = max_loc
    # 矩形右下角点位置
    _x, _y = x + tp_width, y + tp_height
    # 绘制矩形
    bg = bg.copy()
    cv2.rectangle(bg, (x, y), (_x, _y), (0, 0, 255), 2)
    # 显示缺口识别结果
    if im_show:
        imshow(bg)
    return distance


def imshow(img, winname='test', delay=0):
    """cv2展示图片"""
    cv2.imshow(winname, img)
    cv2.waitKey(delay)
    cv2.destroyAllWindows()


class Params(BaseModel):
    image1: str
    image2: str


async def puzzle(request: Request) -> int:
    # 解码Base64字符串
    # 将数据转换为NumPy数组
    # 使用cv2.imdecode将NumPy数组转换为图像
    params = parse_qs(await request.body())
    image1 = params.get(b'image1') or [b'']
    image2 = params.get(b'image2') or [b'']
    file = Image.open(BytesIO(base64.b64decode(image1[0])))
    block = cv2.cvtColor(np.asarray(file), cv2.COLOR_RGB2BGR)
    file = Image.open(BytesIO(base64.b64decode(image2[0])))
    bg = cv2.cvtColor(np.asarray(file), cv2.COLOR_RGB2BGR)
    # imshow(block)
    # imshow(bg)
    # block = cv2.imdecode( np.frombuffer(base64.b64decode(images[0]), np.uint8), cv2.IMREAD_COLOR)
    # bg = cv2.imdecode( np.frombuffer(base64.b64decode(images[1]), np.uint8), cv2.IMREAD_COLOR)
    # cv2.imshow("Title", bg)
    distance = get_distance(block, bg)
    return distance
