"""
客户端接口（无需 JWT，但必须携带数字签名；参数全部白名单校验）。

签名算法：sign = HMAC-SHA256(CLIENT_API_SECRET, '字段1|字段2|...|timestamp') hex 小写
  - register-device : device_code|timestamp
  - bind-card / poll: card_key|device_code|timestamp
  - prompts/ads/config（GET）: device_code|timestamp

业务错误返回 HTTP 200 + {code: 负数, message}，见 README 错误码表。
"""
import time

from django.db.models import Q
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.cards import services
from apps.cards.models import Device
from apps.configs.models import SysConfig
from apps.core.utils import now_ts_ms
from apps.prompts.models import Category, Prompt, Tag


class ClientThrottle(ScopedRateThrottle):
    throttle_scope = 'client'


class ClientBaseView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ClientThrottle]

    @staticmethod
    def _server_time():
        return {'server_time': now_ts_ms()}

    def _verify(self, data, fields):
        services.verify_signature(data, fields)


def envelope(data=None, message='ok'):
    return Response({'code': 0, 'message': message, 'data': data})


class RegisterDeviceView(ClientBaseView):
    """客户端首次运行：注册设备账号。"""

    def post(self, request):
        payload = request.data or {}
        self._verify(payload, ['device_code'])
        device, created = services.get_or_create_device(payload.get('device_code'))
        return envelope({
            'device_code': device.code,
            'is_new': created,
            **self._server_time(),
        })


class BindCardView(ClientBaseView):
    """卡密绑定：校验有效期/是否绑定其他设备。"""

    def post(self, request):
        payload = request.data or {}
        self._verify(payload, ['card_key', 'device_code'])
        card, created = services.bind_card(payload.get('card_key'), payload.get('device_code'))
        return envelope({
            **services.card_brief(card),
            'bound': True,
            'is_new_bind': created,
            **self._server_time(),
        })


class PollView(ClientBaseView):
    """客户端按自定义间隔轮询卡密状态；不记录日志。"""

    def post(self, request):
        payload = request.data or {}
        self._verify(payload, ['card_key', 'device_code'])
        card, remaining = services.poll_card(payload.get('card_key'), payload.get('device_code'))
        return envelope({
            **services.card_brief(card),
            'remaining_seconds': remaining,
            **self._server_time(),
        })


class ClientPromptListView(ClientBaseView):
    """拉取启用中的提示词（可选分类/标签/关键词过滤）。"""

    def get(self, request):
        params = request.query_params
        self._verify(params, ['device_code'])
        qs = (Prompt.objects.filter(status=1)
              .prefetch_related('categories', 'tags').order_by('-id')[:200])
        keyword = (params.get('keyword') or '').strip()[:50]
        if keyword:
            qs = qs.filter(Q(name__icontains=keyword) | Q(content__icontains=keyword))
        category_id = params.get('category_id')
        if category_id and str(category_id).isdigit():
            qs = qs.filter(categories__id=int(category_id))
        tag_id = params.get('tag_id')
        if tag_id and str(tag_id).isdigit():
            qs = qs.filter(tags__id=int(tag_id))
        items = [{
            'id': p.pk, 'name': p.name, 'content': p.content, 'link': p.link,
            'categories': [c.name for c in p.categories.all()],
            'tags': [t.name for t in p.tags.all()],
            'updated_at': p.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        } for p in qs]
        return envelope({'items': items, **self._server_time()})


class ClientAdListView(ClientBaseView):
    """拉取某广告位当前有效的图片。"""

    def get(self, request):
        params = request.query_params
        self._verify(params, ['device_code'])
        from apps.ads.models import AdSlot
        slot_code = (params.get('slot_code') or '').strip()[:64]
        if not slot_code:
            return envelope({'items': [], **self._server_time()})
        now = timezone.now()
        slot = (AdSlot.objects.filter(code=slot_code, status=1)
                .filter(Q(start_time__isnull=True) | Q(start_time__lte=now))
                .filter(Q(end_time__isnull=True) | Q(end_time__gte=now)).first())
        if slot is None:
            return envelope({'items': [], **self._server_time()})
        images = (slot.images.filter(is_valid=True)
                  .filter(Q(start_time__isnull=True) | Q(start_time__lte=now))
                  .filter(Q(end_time__isnull=True) | Q(end_time__gte=now))
                  .order_by('-id')[:50])
        items = [{
            'id': img.pk, 'name': img.name, 'subtitle': img.subtitle, 'url': img.url,
            'images': [p for p in (img.image.url if img.image else None,
                                   img.image2.url if img.image2 else None) if p],
        } for img in images]
        return envelope({'slot': {'name': slot.name, 'code': slot.code}, 'items': items, **self._server_time()})


class ClientConfigView(ClientBaseView):
    """按编码拉取启用中的配置（如 ak/sk），内容不脱敏。"""

    def get(self, request):
        params = request.query_params
        self._verify(params, ['device_code'])
        code = (params.get('code') or '').strip()[:64]
        now = timezone.now()
        conf = (SysConfig.objects.filter(code=code, status=1)
                .filter(Q(start_time__isnull=True) | Q(start_time__lte=now))
                .filter(Q(end_time__isnull=True) | Q(end_time__gte=now)).first())
        if conf is None:
            return envelope({'config': None, **self._server_time()})
        return envelope({'config': {'code': conf.code, 'name': conf.name, 'content': conf.content},
                         **self._server_time()})
