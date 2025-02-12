from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Topic(models.Model): # 用户学习学习主题
    text = models.CharField(max_length=200)
    date_added = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self): # 返回模型的字符串表示
        return self.text 

class Entry(models.Model): # 学到的有关某个主题的具体知识
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE) # 将每个条目关联到特定的主题,并分配一个ID。第二个实参让Django在删除主题时也会删除相关联的条目
    text = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta: # 储存用于管理模型的额外信息
        verbose_name_plural = 'entries'

    def __str__(self): # 返回一个表示条目的简单字符串
        if len(self.text) > 50:
            strnumber = f"{self.text[:50]}..."
        else:
            strnumber = self.text
        return strnumber