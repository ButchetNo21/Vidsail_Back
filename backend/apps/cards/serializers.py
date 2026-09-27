from rest_framework import serializers

from apps.cards.keys import generate_card_key
from apps.cards.models import CardKey, CardLog
from apps.core.exceptions import ValidationError


class CardSerializer(serializers.ModelSerializer):
    device_code = serializers.CharField(source='device.code', read_only=True, default=None)
    status_label = serializers.SerializerMethodField()
    effective_status = serializers.IntegerField(read_only=True)

    class Meta:
        model = CardKey
        fields = [
            'id', 'key', 'status', 'effective_status', 'status_label', 'device_code', 'bound_at',
            'start_time', 'end_time', 'amount', 'remark', 'created_at', 'updated_at',
        ]
        read_only_fields = ['key', 'status', 'bound_at', 'device']

    def get_status_label(self, obj):
        return CardKey.STATUS_MAP.get(obj.effective_status, '未知')


class CardCreateSerializer(serializers.Serializer):
    count = serializers.IntegerField(min_value=1, max_value=100, required=False, default=1)
    start_time = serializers.DateTimeField(required=False, allow_null=True)
    end_time = serializers.DateTimeField(required=False, allow_null=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)
    remark = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')

    def validate(self, attrs):
        start, end = attrs.get('start_time'), attrs.get('end_time')
        if start and end and start >= end:
            raise ValidationError('开始时间必须早于结束时间')
        return attrs

    def create_fields(self):
        return {
            'start_time': self.validated_data.get('start_time'),
            'end_time': self.validated_data.get('end_time'),
            'amount': self.validated_data.get('amount', 0),
            'remark': self.validated_data.get('remark', ''),
        }


class CardUpdateSerializer(serializers.ModelSerializer):
    """卡密只能改业务字段，密钥不可修改。"""

    class Meta:
        model = CardKey
        fields = ['start_time', 'end_time', 'amount', 'remark']

    def validate(self, attrs):
        start = attrs.get('start_time', getattr(self.instance, 'start_time', None))
        end = attrs.get('end_time', getattr(self.instance, 'end_time', None))
        if start and end and start >= end:
            raise ValidationError('开始时间必须早于结束时间')
        return attrs


class CardLogSerializer(serializers.ModelSerializer):
    card_key = serializers.CharField(source='card.key', read_only=True)

    class Meta:
        model = CardLog
        fields = ['id', 'card_key', 'action', 'source', 'operator_name', 'detail', 'created_at']
