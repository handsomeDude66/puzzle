from rest_framework import serializers

from .models import *


class LoginIn(serializers.Serializer):
    """登录"""
    username = serializers.CharField()
    password = serializers.CharField()


class PuzzleIn(serializers.Serializer):
    """图片解析"""
    image1 = serializers.CharField()
    image2 = serializers.CharField()


class PasswordOut(serializers.ModelSerializer):
    """卡密"""
    class Meta:
        model = Password
        fields = '__all__'


class PasswordIn(serializers.ModelSerializer):
    """导入卡密"""
    class Meta:
        model = Password
        fields = ['expiry_time']


class PasswordBindIn(serializers.Serializer):
    """卡密绑定"""
    device_id = serializers.CharField()


class PasswordUnbindIn(serializers.Serializer):
    """卡密绑定"""
    device_id = serializers.PrimaryKeyRelatedField(
        queryset=Device.objects.all())
