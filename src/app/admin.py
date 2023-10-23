from django.contrib import admin

from .models import *

# Register your models here.


class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'first_name', 'last_name', 'email')


class DeviceAdmin(admin.ModelAdmin):
    list_display = ('id',)


class PasswordAdmin(admin.ModelAdmin):
    list_display = ('id', 'expiry_time', 'display_devices')

    def display_devices(self, obj: Password):
        return f"[{', '.join([repr(i.id) for i in obj.devices.all()])}]"

    display_devices.short_description = '绑定的设备'


admin.site.register(User, UserAdmin)
admin.site.register(Device, DeviceAdmin)
admin.site.register(Password, PasswordAdmin)
