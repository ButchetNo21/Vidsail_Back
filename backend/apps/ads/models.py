from django.db import models

from apps.core.models import BaseModel


class AdSlot(BaseModel):
    """广告位：先建占位，再往里加图片。"""

    name = models.CharField(max_length=64, verbose_name='广告位名称')
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name='唯一编码')
    remark = models.CharField(max_length=255, blank=True, default='', verbose_name='备注')
    start_time = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    status = models.SmallIntegerField(default=1, choices=[(1, '启用'), (0, '停用')], verbose_name='状态')

    class Meta:
        db_table = 'ad_slot'
        ordering = ['-id']
        verbose_name = '广告位'

    def __str__(self):
        return f'{self.name}({self.code})'


def ad_image_path(instance, filename):
    import uuid
    from datetime import datetime
    ext = (filename.rsplit('.', 1)[-1] or 'png').lower()
    return 'ads/%s/%s.%s' % (datetime.now().strftime('%Y%m'), uuid.uuid4().hex[:16], ext)


class AdImage(BaseModel):
    """广告图片：一个记录最多两张图（image 主图 + image2 副图）。"""

    slot = models.ForeignKey(AdSlot, on_delete=models.CASCADE, related_name='images', verbose_name='所属广告位')
    name = models.CharField(max_length=64, verbose_name='图片名称')
    subtitle = models.CharField(max_length=128, blank=True, default='', verbose_name='副标题')
    image = models.ImageField(upload_to=ad_image_path, null=True, blank=True, verbose_name='主图')
    image2 = models.ImageField(upload_to=ad_image_path, null=True, blank=True, verbose_name='副图')
    remark = models.CharField(max_length=255, blank=True, default='', verbose_name='备注')
    url = models.CharField(max_length=255, blank=True, default='', verbose_name='跳转链接')
    is_valid = models.BooleanField(default=True, verbose_name='是否有效')
    start_time = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')

    class Meta:
        db_table = 'ad_image'
        ordering = ['-id']
        verbose_name = '广告图片'

    def __str__(self):
        return self.name
