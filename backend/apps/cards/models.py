from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class Device(BaseModel):
    """客户端设备。设备码由客户端首次运行时生成并注册，全局唯一。"""

    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name='设备账号')
    remark = models.CharField(max_length=255, blank=True, default='', verbose_name='备注')
    status = models.SmallIntegerField(default=0, choices=[(0, '正常'), (1, '禁用')], verbose_name='状态')
    last_seen_at = models.DateTimeField(null=True, blank=True, verbose_name='最近在线时间')

    class Meta:
        db_table = 'card_device'
        ordering = ['-id']
        verbose_name = '设备'

    def __str__(self):
        return self.code


class CardKey(BaseModel):
    """卡密：16 位大写字母数字，服务端生成，绑定设备后生效。"""

    STATUS_UNBOUND = 0
    STATUS_BOUND = 1
    STATUS_INVALID = 3
    STATUS_CHOICES = ((0, '未绑定'), (1, '已绑定'), (3, '已失效'))
    STATUS_MAP = {0: '未绑定', 1: '已绑定', 2: '已过期', 3: '已失效'}

    key = models.CharField(max_length=16, unique=True, db_index=True, verbose_name='卡密')
    device = models.ForeignKey(Device, null=True, blank=True, on_delete=models.SET_NULL,
                               related_name='cards', verbose_name='绑定设备')
    start_time = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='金额')
    remark = models.CharField(max_length=255, blank=True, default='', verbose_name='备注')
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=0, db_index=True, verbose_name='状态')
    bound_at = models.DateTimeField(null=True, blank=True, verbose_name='绑定时间')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name='created_cards', verbose_name='创建人')

    class Meta:
        db_table = 'card_key'
        ordering = ['-id']
        verbose_name = '卡密'

    def __str__(self):
        return self.key

    @property
    def is_expired(self):
        """结束时间已过即视为过期（无论是否绑定）。"""
        if not self.end_time:
            return False
        from django.utils import timezone
        return timezone.now() > self.end_time

    @property
    def effective_status(self):
        """对外状态：0 未绑定 / 1 已绑定 / 2 已过期 / 3 已失效。"""
        if self.status == self.STATUS_INVALID:
            return 3
        if self.is_expired:
            return 2
        return self.status


class CardLog(BaseModel):
    """卡密操作日志：创建/修改/取消/绑定/解绑；轮询不记录。"""

    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_CANCEL = 'cancel'
    ACTION_BIND = 'bind'
    ACTION_UNBIND = 'unbind'
    ACTION_CHOICES = (
        (ACTION_CREATE, '创建'), (ACTION_UPDATE, '修改'), (ACTION_CANCEL, '取消'),
        (ACTION_BIND, '绑定'), (ACTION_UNBIND, '解绑'),
    )
    SOURCE_CHOICES = (('admin', '后台'), ('client', '客户端'))

    card = models.ForeignKey(CardKey, on_delete=models.CASCADE, related_name='logs', verbose_name='卡密')
    action = models.CharField(max_length=16, choices=ACTION_CHOICES, verbose_name='动作')
    source = models.CharField(max_length=8, choices=SOURCE_CHOICES, verbose_name='来源')
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name='card_logs', verbose_name='操作人')
    operator_name = models.CharField(max_length=64, blank=True, default='', verbose_name='操作人名称')
    detail = models.JSONField(default=dict, blank=True, verbose_name='详情')

    class Meta:
        db_table = 'card_log'
        ordering = ['-id']
        verbose_name = '卡密日志'
