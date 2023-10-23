from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils import timezone

from common.validators import v_time_gt_now

# Create your models here.


class User(AbstractUser):
    objects: UserManager

    class Meta:
        db_table = 'user'


class Device(models.Model):
    """设备"""
    id = models.CharField('设备ID', primary_key=True, max_length=16)


class Password(models.Model):
    """卡密"""
    id = models.CharField('卡密', primary_key=True, max_length=16)
    expiry_time = models.DateTimeField('卡密过期时间', validators=[v_time_gt_now])
    devices = models.ManyToManyField(Device)

    class Meta:
        db_table = 'password'

    def is_valid(self):
        """是否有效"""
        return timezone.now() < self.expiry_time
