import datetime as dt

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def v_time_gt_now(value: dt.date):
    if not value > timezone.now():
        raise ValidationError(_('时间不能小于当前时间'))


def v_min(length: int):
    def wrapper(value):
        if len(value) < length:
            raise ValidationError(_('长度不能小于{0}').format(length))
    return wrapper
