import re

from rest_framework import serializers

from apps.configs.models import SysConfig
from apps.core.exceptions import ValidationError

CODE_RE = re.compile(r'^[A-Za-z0-9_-]{2,64}$')


class SysConfigListSerializer(serializers.ModelSerializer):
    """列表用：内容脱敏。"""

    class Meta:
        model = SysConfig
        fields = ['id', 'name', 'code', 'content', 'status', 'remark',
                  'start_time', 'end_time', 'created_at', 'updated_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['content'] = '******' if instance.content else ''
        return data


class SysConfigDetailSerializer(serializers.ModelSerializer):
    """创建/编辑/详情用：内容明文。编码创建后不可修改。"""

    class Meta:
        model = SysConfig
        fields = ['id', 'name', 'code', 'content', 'status', 'remark',
                  'start_time', 'end_time', 'created_at', 'updated_at']

    def validate_code(self, value):
        if not CODE_RE.match(value):
            raise ValidationError('编码只能包含字母、数字、下划线、中划线，长度2-64')
        if self.instance:
            if value != self.instance.code:
                raise ValidationError('编码创建后不可修改')
            return value
        if SysConfig.all_objects.filter(code=value).exists():
            raise ValidationError('编码已存在')
        return value

    def validate(self, attrs):
        start = attrs.get('start_time', getattr(self.instance, 'start_time', None))
        end = attrs.get('end_time', getattr(self.instance, 'end_time', None))
        if start and end and start >= end:
            raise ValidationError('开始时间必须早于结束时间')
        return attrs
