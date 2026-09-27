from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.cards.keys import generate_card_key
from apps.cards.models import CardKey, CardLog
from apps.cards.serializers import CardCreateSerializer, CardLogSerializer, CardSerializer, CardUpdateSerializer
from apps.core.exceptions import ValidationError
from apps.core.views import PermViewSet, apply_ordering, parse_date_param


def status_q(status_value):
    """按对外状态过滤：0 未绑定 / 1 已绑定 / 2 已过期 / 3 已失效。"""
    now = timezone.now()
    not_expired = Q(end_time__isnull=True) | Q(end_time__gte=now)
    if status_value == 0:
        return Q(status=CardKey.STATUS_UNBOUND) & not_expired
    if status_value == 1:
        return Q(status=CardKey.STATUS_BOUND) & not_expired
    if status_value == 2:
        return ~Q(status=CardKey.STATUS_INVALID) & Q(end_time__lt=now)
    if status_value == 3:
        return Q(status=CardKey.STATUS_INVALID)
    return Q()


def _json_safe(value):
    if isinstance(value, str):
        return value
    return str(value)


def log_card_action(card, action, source, operator=None, operator_name='', detail=None):
    CardLog.objects.create(
        card=card, action=action, source=source, operator=operator,
        operator_name=operator_name or (operator.username if operator else ''),
        detail=detail or {},
    )


def build_diff(instance, validated_data):
    diff = {}
    for field, new in validated_data.items():
        old = getattr(instance, field)
        if old != new:
            diff[field] = [_json_safe(old), _json_safe(new)]
    return diff


class CardViewSet(PermViewSet):
    permission_classes = PermViewSet.permission_classes
    perm_map = {
        'list': 'card:view', 'retrieve': 'card:view',
        'create': 'card:edit', 'update': 'card:edit', 'partial_update': 'card:edit',
        'unbind': 'card:edit', 'cancel': 'card:cancel',
    }
    queryset = CardKey.objects.all()
    serializer_class = CardSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']

    def get_serializer_class(self):
        if self.action in ('update', 'partial_update'):
            return CardUpdateSerializer
        return CardSerializer

    def filter_queryset(self, qs):
        params = self.request.query_params
        keyword = (params.get('keyword') or '').strip()
        if keyword:
            qs = qs.filter(Q(key__icontains=keyword) | Q(device__code__icontains=keyword))
        status_value = params.get('status')
        if status_value not in (None, ''):
            try:
                qs = qs.filter(status_q(int(status_value)))
            except (TypeError, ValueError):
                pass
        created_from = parse_date_param(params.get('created_from'))
        created_to = parse_date_param(params.get('created_to'), end_of_day=True)
        if created_from:
            qs = qs.filter(created_at__gte=created_from)
        if created_to:
            qs = qs.filter(created_at__lte=created_to)
        return apply_ordering(qs, self.request, {'created_at', 'amount', 'end_time'}, ['-id'])

    def create(self, request, *args, **kwargs):
        ser = CardCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        count = ser.validated_data['count']
        fields = ser.create_fields()
        cards = []
        for _ in range(count):
            card = CardKey.objects.create(key=generate_card_key(), created_by=request.user, **fields)
            log_card_action(card, CardLog.ACTION_CREATE, 'admin', operator=request.user,
                            detail={k: _json_safe(v) for k, v in fields.items()})
            cards.append(card)
        return Response(CardSerializer(cards, many=True).data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        diff = build_diff(serializer.instance, serializer.validated_data)
        card = serializer.save()
        if diff:
            log_card_action(card, CardLog.ACTION_UPDATE, 'admin', operator=self.request.user, detail=diff)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消卡密 -> 已失效。"""
        card = self.get_object()
        if card.status == CardKey.STATUS_INVALID:
            raise ValidationError('卡密已是失效状态')
        card.status = CardKey.STATUS_INVALID
        card.save(update_fields=['status', 'updated_at'])
        log_card_action(card, CardLog.ACTION_CANCEL, 'admin', operator=request.user)
        return Response(CardSerializer(card).data)

    @action(detail=True, methods=['post'])
    def unbind(self, request, pk=None):
        """解绑设备。"""
        card = self.get_object()
        if card.status != CardKey.STATUS_BOUND or not card.device:
            raise ValidationError('卡密当前未绑定设备')
        old_device = card.device.code
        card.device = None
        card.status = CardKey.STATUS_UNBOUND
        card.bound_at = None
        card.save(update_fields=['device', 'status', 'bound_at', 'updated_at'])
        log_card_action(card, CardLog.ACTION_UNBIND, 'admin', operator=request.user,
                        detail={'device_code': old_device})
        return Response(CardSerializer(card).data)


class CardLogViewSet(PermViewSet):
    perm_map = {'list': 'cardlog:view'}
    queryset = CardLog.objects.select_related('card').all()
    serializer_class = CardLogSerializer
    http_method_names = ['get', 'head', 'options']

    def filter_queryset(self, qs):
        params = self.request.query_params
        keyword = (params.get('keyword') or '').strip()
        if keyword:
            qs = qs.filter(Q(card__key__icontains=keyword) | Q(operator_name__icontains=keyword))
        action_name = params.get('action')
        if action_name:
            qs = qs.filter(action=action_name)
        source = params.get('source')
        if source:
            qs = qs.filter(source=source)
        created_from = parse_date_param(params.get('created_from'))
        created_to = parse_date_param(params.get('created_to'), end_of_day=True)
        if created_from:
            qs = qs.filter(created_at__gte=created_from)
        if created_to:
            qs = qs.filter(created_at__lte=created_to)
        return apply_ordering(qs, self.request, {'created_at'}, ['-id'])
