import base64
import datetime
import os
from urllib.parse import parse_qs
from io import BytesIO
from pathlib import Path
import uuid

import cv2
from cv2.typing import MatLike
import numpy as np
from flask import Flask, request
from pydantic import BaseModel,Base64Str
from PIL import Image
from fastapi import Depends, FastAPI, Form, Header, Query, Request

# class Item(BaseModel):
#     name: str
#     age: int

app = FastAPI()

# @app.get("/items/")
# def create_item(item: Item = Depends()):
#     return item.dict()

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
    print(distance)
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

@app.post("/puzzle/")
async def puzzle(param: Params):
    # print(image1)
    # 解码Base64字符串
    # 将数据转换为NumPy数组
    # 使用cv2.imdecode将NumPy数组转换为图像
    file = Image.open(BytesIO(base64.b64decode(param.image1)))
    block = cv2.cvtColor(np.asarray(file), cv2.COLOR_RGB2BGR)
    file = Image.open(BytesIO(base64.b64decode(param.image2)))
    bg = cv2.cvtColor(np.asarray(file), cv2.COLOR_RGB2BGR)
    # base64_to_img(block, bg)
    # imshow(block)
    # imshow(bg)
    # block = cv2.imdecode( np.frombuffer(base64.b64decode(image1), np.uint8), cv2.IMREAD_COLOR)
    # bg = cv2.imdecode( np.frombuffer(base64.b64decode(image2), np.uint8), cv2.IMREAD_COLOR)
    # cv2.imshow("Title", bg)
    distance = get_distance(block, bg)
    print(distance)
    return distance

def base64_to_img(bstr1, bstr2, dir_path="./test/"):
    
    now = datetime.datetime.now()

    timestamp = now.strftime("%Y_%m_%d_%H:%M")
    imgdata1 = base64.b64decode(bstr1)
    imgdata2 = base64.b64decode(bstr2)
    file_name1 =  str(uuid.uuid4()) +".png"  # 使用UUID生成文件名
    file_name2 =  str(uuid.uuid4()) +".png"  # 使用UUID生成文件名
    print(file_name1)
    print(file_name2)
    file_path1 = os.path.join(dir_path, file_name1)
    file_path2 = os.path.join(dir_path, file_name2)
    with open(file_path1, 'wb') as f:
        f.write(imgdata1)
    with open(file_path2, 'wb') as f:
        f.write(imgdata2)

@app.get("/puzzle/")
def sb():
    return '别用get了,想要源码直接来找我好吗北鼻'

@app.post("/isKm")
def isKm():
    pass
