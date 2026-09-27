from django.db.models import Count, Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.ads.models import AdImage, AdSlot
from apps.ads.serializers import AdImageSerializer, AdSlotSerializer, ImageUploadSerializer
from apps.core.views import PermViewSet, apply_ordering, parse_date_param


class AdSlotViewSet(PermViewSet):
    perm_map = {
        'list': 'ad:view', 'retrieve': 'ad:view',
        'create': 'ad:edit', 'update': 'ad:edit', 'partial_update': 'ad:edit', 'destroy': 'ad:edit',
    }
    queryset = AdSlot.objects.all()
    serializer_class = AdSlotSerializer

    def get_queryset(self):
        qs = AdSlot.objects.annotate(image_count=Count('images', distinct=True))
        params = self.request.query_params
        keyword = (params.get('keyword') or '').strip()
        if keyword:
            qs = qs.filter(Q(name__icontains=keyword) | Q(code__icontains=keyword))
        status_value = params.get('status')
        if status_value in ('0', '1'):
            qs = qs.filter(status=int(status_value))
        return apply_ordering(qs, self.request, {'created_at', 'name'}, ['-id'])

    def validate_time_range(self, attrs, instance=None):
        start = attrs.get('start_time', getattr(instance, 'start_time', None))
        end = attrs.get('end_time', getattr(instance, 'end_time', None))
        if start and end and start >= end:
            from apps.core.exceptions import ValidationError
            raise ValidationError('开始时间必须早于结束时间')

    def perform_create(self, serializer):
        self.validate_time_range(serializer.validated_data)
        serializer.save()

    def perform_update(self, serializer):
        self.validate_time_range(serializer.validated_data, serializer.instance)
        serializer.save()


class AdImageViewSet(PermViewSet):
    perm_map = {
        'list': 'ad:view', 'retrieve': 'ad:view',
        'create': 'ad:edit', 'update': 'ad:edit', 'partial_update': 'ad:edit', 'destroy': 'ad:edit',
        'upload': 'ad:edit', 'remove_image': 'ad:edit',
    }
    queryset = AdImage.objects.select_related('slot').all()
    serializer_class = AdImageSerializer

    def filter_queryset(self, qs):
        params = self.request.query_params
        slot_id = params.get('slot')
        if slot_id and slot_id.isdigit():
            qs = qs.filter(slot_id=int(slot_id))
        keyword = (params.get('keyword') or '').strip()
        if keyword:
            qs = qs.filter(Q(name__icontains=keyword) | Q(subtitle__icontains=keyword))
        valid_param = params.get('is_valid')
        if valid_param in ('0', '1'):
            qs = qs.filter(is_valid=valid_param == '1')
        return apply_ordering(qs, self.request, {'created_at'}, ['-id'])

    def validate_time_range(self, attrs, instance=None):
        start = attrs.get('start_time', getattr(instance, 'start_time', None))
        end = attrs.get('end_time', getattr(instance, 'end_time', None))
        if start and end and start >= end:
            from apps.core.exceptions import ValidationError
            raise ValidationError('开始时间必须早于结束时间')

    def perform_create(self, serializer):
        self.validate_time_range(serializer.validated_data)
        serializer.save()

    def perform_update(self, serializer):
        self.validate_time_range(serializer.validated_data, serializer.instance)
        serializer.save()

    @action(detail=True, methods=['post'])
    def upload(self, request, pk=None):
        """上传/替换图片：multipart(file, position=image|image2)。"""
        image = self.get_object()
        ser = ImageUploadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        image = ser.save(image)
        return Response(AdImageSerializer(image).data)

    @action(detail=True, methods=['post'])
    def remove_image(self, request, pk=None):
        """移除某一张图。"""
        image = self.get_object()
        position = request.data.get('position')
        if position not in ('image', 'image2'):
            from apps.core.exceptions import ValidationError
            raise ValidationError('position 必须是 image 或 image2')
        setattr(image, position, None)
        image.save(update_fields=[position, 'updated_at'])
        return Response(AdImageSerializer(image).data)
