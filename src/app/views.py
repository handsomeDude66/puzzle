import base64
import random
import string
from io import BytesIO

import cv2
import numpy as np
from cv2.typing import MatLike
from django.http import HttpRequest
from django.contrib.auth import authenticate, login
from drf_yasg import openapi
from PIL import Image
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from common.restapi import restapi

from .models import *
from .serializers import *

# Create your views here.


class LoginView(APIView):
    @restapi(body=LoginIn, response=openapi.Response('是否成功', openapi.Schema(type=openapi.TYPE_BOOLEAN)))
    def post(self, request: HttpRequest, data: dict):
        user = authenticate(request, **data)
        if user is None:
            return False
        login(request, user)
        return True


class PuzzleView(APIView):
    @staticmethod
    def get_distance(tp: MatLike, bg: MatLike):
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
        return distance

    @restapi(query=PuzzleIn, response=openapi.Response('位置', openapi.Schema(type=openapi.TYPE_INTEGER)))
    def post(self, request: HttpRequest, data: dict):
        """拼图滑块所需移动位置"""
        # 解码Base64字符串
        # 将数据转换为NumPy数组
        # 使用cv2.imdecode将NumPy数组转换为图像
        image1 = data.get(b'image1') or [b'']
        image2 = data.get(b'image2') or [b'']
        file = Image.open(BytesIO(base64.b64decode(image1[0])))
        block = cv2.cvtColor(np.asarray(file), cv2.COLOR_RGB2BGR)
        file = Image.open(BytesIO(base64.b64decode(image2[0])))
        bg = cv2.cvtColor(np.asarray(file), cv2.COLOR_RGB2BGR)
        # imshow(block)
        # imshow(bg)
        # block = cv2.imdecode( np.frombuffer(base64.b64decode(images[0]), np.uint8), cv2.IMREAD_COLOR)
        # bg = cv2.imdecode( np.frombuffer(base64.b64decode(images[1]), np.uint8), cv2.IMREAD_COLOR)
        # cv2.imshow("Title", bg)
        distance = self.get_distance(block, bg)
        return distance


class PasswordViewSet(ModelViewSet):
    """卡密"""
    queryset = Password.objects.all()
    serializer_class = PasswordOut

    @restapi(response=PasswordOut(many=True))
    def list(self, request):
        """卡密列表"""
        return super().list(request)

    @restapi(body=PasswordIn, response=PasswordOut)
    def create(self, request, data: dict):
        """创建卡密"""
        obj = Password.objects.create(
            id=''.join(random.choices(string.hexdigits, k=16)),
            **data,
        )
        return PasswordOut(obj).data

    @restapi(response=PasswordOut)
    def retrieve(self, request, pk: str):
        """检索卡密"""
        return super().retrieve(request, pk)

    @restapi(body=PasswordIn, response=PasswordOut)
    def update(self, request, pk: str, serializer: PasswordIn, data: dict):
        """更新卡密"""
        obj = serializer.update(self.get_object(), data)
        return PasswordOut(obj).data

    @restapi()
    def destroy(self, request, pk: str):
        """删除卡密"""
        return super().destroy(request, pk)

    @action(methods=['GET'], detail=True)
    @restapi(response=openapi.Response('是否有效', openapi.Schema(type=openapi.TYPE_BOOLEAN)))
    def is_valid(self, request, pk: str):
        """是否有效"""
        password: Password = self.get_object()
        return password.is_valid()

    @action(methods=['POST'], detail=True)
    @restapi(body=PasswordBindIn, response=openapi.Response('是否成功', openapi.Schema(type=openapi.TYPE_BOOLEAN)))
    def bind(self, request, pk: str, data: dict):
        """卡密设备绑定"""
        password: Password = self.get_object()
        if not password.is_valid() or password.devices.count() >= 3:
            return False
        device, _ = Device.objects.get_or_create(id=data['device_id'])
        password.devices.add(device)
        password.save()
        return True

    @action(methods=['POST'], detail=True)
    @restapi(body=PasswordBindIn)
    def unbind(self, request, pk: str, data: dict):
        """卡密设备解绑"""
        password: Password = self.get_object()
        device = Device.objects.get(id=data['device_id'])
        password.devices.remove(device)
        password.save()
