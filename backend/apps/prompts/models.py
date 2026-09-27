from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class Category(BaseModel):
    """提示词分类。"""

    name = models.CharField(max_length=32, unique=True, verbose_name='分类名称')
    sort = models.IntegerField(default=0, verbose_name='排序')
    status = models.SmallIntegerField(default=1, choices=[(1, '启用'), (0, '停用')], verbose_name='状态')

    class Meta:
        db_table = 'prompt_category'
        ordering = ['sort', '-id']
        verbose_name = '提示词分类'

    def __str__(self):
        return self.name


class Tag(BaseModel):
    """提示词标签。"""

    name = models.CharField(max_length=32, unique=True, verbose_name='标签名称')
    sort = models.IntegerField(default=0, verbose_name='排序')
    status = models.SmallIntegerField(default=1, choices=[(1, '启用'), (0, '停用')], verbose_name='状态')

    class Meta:
        db_table = 'prompt_tag'
        ordering = ['sort', '-id']
        verbose_name = '提示词标签'

    def __str__(self):
        return self.name


class Prompt(BaseModel):
    """
    提示词。content 为 TEXT，可包含换行；前端展示时用纯文本渲染（Vue 默认转义，无 XSS）。
    """

    name = models.CharField(max_length=64, verbose_name='提示词名称')
    content = models.TextField(max_length=20000, verbose_name='提示词内容/Skills')
    link = models.CharField(max_length=255, blank=True, default='', verbose_name='关联链接')
    categories = models.ManyToManyField(Category, blank=True, related_name='prompts', verbose_name='分类')
    tags = models.ManyToManyField(Tag, blank=True, related_name='prompts', verbose_name='标签')
    status = models.SmallIntegerField(default=1, choices=[(1, '启用'), (0, '停用')], verbose_name='状态')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name='created_prompts', verbose_name='创建人')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name='updated_prompts', verbose_name='修改人')

    class Meta:
        db_table = 'prompt'
        ordering = ['-id']
        verbose_name = '提示词'

    def __str__(self):
        return self.name
