from django.contrib import admin

from .models import Topic, Entry

# Register your models here.
admin.site.register(Topic) # 让超级用户可以管理此模型
admin.site.register(Entry)