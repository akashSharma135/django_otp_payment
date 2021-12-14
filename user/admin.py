from django.contrib import admin
from .models import CustomUser, Otp

admin.site.register(CustomUser)
admin.site.register(Otp)
