import base64
import datetime
import os
from urllib.parse import parse_qs
from io import BytesIO
from pathlib import Path
import uuid
from paddleocr import PaddleOCR

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

os.environ['KMP_DUPLICATE_LIB_OK'] = 'True' 
ocr = PaddleOCR(use_angle_cls=False, use_gpu=False,
            lang="ch", show_log=False)  # need to run only once to download and load model into memory


class FindOne(BaseModel):
    txt : str
    image: str




@app.post("/findOne/")
async def findOne(param: FindOne):
    try:
        text = param.txt
        base64_image = param.image

        # 解码base64图像
        image_data = base64.b64decode(base64_image)
        image_data = np.fromstring(image_data, np.uint8)

        # 将数据转换为OpenCV图像
        img = cv2.imdecode(image_data, cv2.IMREAD_UNCHANGED)

        # 现在你可以使用img变量进行OCR识别
        ocr_text = ocr.ocr(img, cls=False)

        coordinates_list = []
        for line in ocr_text:
            for word_info in line:
                line_text = ' '.join(str(i) for i in word_info[-1])
                if text in line_text:  # 这里改为包含判断
                    print("识别的文字：", text)
                    print("坐标：", word_info[0])
                    coordinates = word_info[0]
                    second_coordinate = coordinates[1]
                    coordinates_list.append({"x": second_coordinate[0], "y": second_coordinate[1]})

        # 如果text包含"提交订单"，并且有多个匹配，选择第二个
        if "提交订单" in text and len(coordinates_list) > 1:
            print("提交订单第二位")
            return coordinates_list[1]
        # 其他情况下，如果有匹配，选择第一个
        elif coordinates_list:
            return coordinates_list[0]
        else:
            print("没有找到匹配的文字")
            # return "没有找到匹配的文字"
    except Exception:
        return ""