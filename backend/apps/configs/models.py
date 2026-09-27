from django.db import models

from apps.core.models import BaseModel


class SysConfig(BaseModel):
    """系统配置：存放 ak/sk 之类的账号数据。列表页内容脱敏，详情页可见。"""

    name = models.CharField(max_length=64, verbose_name='配置名称')
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name='唯一编码')
    content = models.TextField(blank=True, default='', verbose_name='内容')
    status = models.SmallIntegerField(default=1, choices=[(1, '启用'), (0, '停用')], verbose_name='状态')
    remark = models.CharField(max_length=255, blank=True, default='', verbose_name='备注')
    start_time = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')

    class Meta:
        db_table = 'sys_config'
        ordering = ['-id']
        verbose_name = '系统配置'

    def __str__(self):
        return f'{self.name}({self.code})'
