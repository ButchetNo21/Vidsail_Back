from rest_framework import serializers

from apps.ads.models import AdImage, AdSlot

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB


class AdSlotSerializer(serializers.ModelSerializer):
    image_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = AdSlot
        fields = ['id', 'name', 'code', 'remark', 'start_time', 'end_time', 'status',
                  'image_count', 'created_at', 'updated_at']


class AdImageSerializer(serializers.ModelSerializer):
    slot_name = serializers.CharField(source='slot.name', read_only=True, default='')
    image_url = serializers.SerializerMethodField()
    image2_url = serializers.SerializerMethodField()

    class Meta:
        model = AdImage
        fields = ['id', 'slot', 'slot_name', 'name', 'subtitle', 'image', 'image_url',
                  'image2', 'image2_url', 'remark', 'url', 'is_valid', 'start_time', 'end_time',
                  'created_at', 'updated_at']
        read_only_fields = ['image', 'image2']

    def get_image_url(self, obj):
        return obj.image.url if obj.image else None

    def get_image2_url(self, obj):
        return obj.image2.url if obj.image2 else None


class ImageUploadSerializer(serializers.Serializer):
    """图片上传：position=image|image2，单张最大 5MB。"""
    POSITION_CHOICES = (('image', '主图'), ('image2', '副图'))

    file = serializers.ImageField()
    position = serializers.ChoiceField(choices=POSITION_CHOICES)

    def validate_file(self, value):
        if value.size > MAX_IMAGE_SIZE:
            raise serializers.ValidationError('图片不能超过5MB')
        return value

    def save(self, instance):
        position = self.validated_data['position']
        setattr(instance, position, self.validated_data['file'])
        instance.save(update_fields=[position, 'updated_at'])
        return instance
