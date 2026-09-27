from django.db import models
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    """默认过滤掉已软删除的数据。"""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='修改时间')
    deleted_at = models.DateTimeField(null=True, blank=True, editable=False, verbose_name='删除时间')

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """软删除。"""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at', 'updated_at'])
