from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response

from apps.configs.models import SysConfig
from apps.configs.serializers import SysConfigDetailSerializer, SysConfigListSerializer
from apps.core.views import PermViewSet, apply_ordering, parse_date_param


class SysConfigViewSet(PermViewSet):
    perm_map = {
        'list': 'config:view', 'retrieve': 'config:view',
        'create': 'config:edit', 'update': 'config:edit', 'partial_update': 'config:edit',
        'destroy': 'config:edit',
    }
    queryset = SysConfig.objects.all()
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    def get_serializer_class(self):
        if self.action == 'list':
            return SysConfigListSerializer
        return SysConfigDetailSerializer

    def filter_queryset(self, qs):
        params = self.request.query_params
        keyword = (params.get('keyword') or '').strip()
        if keyword:
            qs = qs.filter(Q(name__icontains=keyword) | Q(code__icontains=keyword))
        status_value = params.get('status')
        if status_value in ('0', '1'):
            qs = qs.filter(status=int(status_value))
        created_from = parse_date_param(params.get('created_from'))
        created_to = parse_date_param(params.get('created_to'), end_of_day=True)
        if created_from:
            qs = qs.filter(created_at__gte=created_from)
        if created_to:
            qs = qs.filter(created_at__lte=created_to)
        return apply_ordering(qs, self.request, {'created_at', 'name'}, ['-id'])

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()  # 软删除
        return Response({'id': instance.pk, 'deleted': True}, status=status.HTTP_200_OK)
