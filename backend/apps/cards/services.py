"""客户端接口业务逻辑：签名校验、设备注册、卡密绑定与轮询。"""
import hashlib
import hmac
import re
import time

from django.conf import settings
from django.utils import timezone

from apps.cards.models import CardKey, Device, CardLog
from apps.core.exceptions import ClientApiError
from apps.cards.keys import is_valid_key_format, normalize_key

DEVICE_CODE_RE = re.compile(r'^[A-Za-z0-9_-]{8,64}$')


# ---------- 签名 ----------
def make_sign(*parts):
    """sign = HMAC-SHA256(CLIENT_API_SECRET, 'p1|p2|...') 的十六进制小写。"""
    message = '|'.join(str(p) for p in parts)
    return hmac.new(settings.CLIENT_API_SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()


def verify_signature(payload, fields):
    """
    payload 中必须包含 timestamp(ms) 与 sign；签名内容 = fields 顺序取值 + timestamp。
    校验失败 -> -1；时间戳超出容差 -> -2。
    """
    ts = payload.get('timestamp')
    sign = payload.get('sign') or ''
    if ts in (None, '') or not sign:
        raise ClientApiError(-1, '缺少签名参数')
    try:
        ts = int(ts)
    except (TypeError, ValueError):
        raise ClientApiError(-1, '时间戳格式错误')

    now_ms = time.time() * 1000
    if abs(now_ms - ts) > settings.CLIENT_TS_TOLERANCE * 1000:
        raise ClientApiError(-2, '请求时间戳已过期，请校准系统时间')

    expected = make_sign(*[payload.get(f) or '' for f in fields], ts)
    if not hmac.compare_digest(expected, str(sign).lower()):
        raise ClientApiError(-1, '签名校验失败')


# ---------- 设备 ----------
def get_or_create_device(code):
    code = (code or '').strip()
    if not DEVICE_CODE_RE.match(code):
        raise ClientApiError(-1, '设备账号格式错误')
    device, created = Device.all_objects.get_or_create(code=code)
    if device.status == 1:
        raise ClientApiError(-8, '设备已被禁用')
    device.last_seen_at = timezone.now()
    device.save(update_fields=['last_seen_at', 'updated_at'])
    return device, created


# ---------- 卡密校验 ----------
def find_card(key, check_format=True):
    key = normalize_key(key)
    if check_format and not is_valid_key_format(key):
        raise ClientApiError(-9, '卡密格式错误')
    card = CardKey.objects.filter(key=key).first()
    if card is None:
        raise ClientApiError(-3, '卡密不存在')
    return card


def check_card_usable(card):
    now = timezone.now()
    if card.status == CardKey.STATUS_INVALID:
        raise ClientApiError(-6, '卡密已失效')
    if card.start_time and now < card.start_time:
        raise ClientApiError(-7, '卡密未到生效时间')
    if card.is_expired:
        raise ClientApiError(-4, '卡密已过期')


def bind_card(card_key, device_code):
    device, _ = get_or_create_device(device_code)
    card = find_card(card_key)
    now = timezone.now()

    if card.status == CardKey.STATUS_BOUND and card.device_id and card.device_id != device.id:
        raise ClientApiError(-5, '卡密已绑定其他设备')

    if card.status == CardKey.STATUS_BOUND and card.device_id == device.id:
        check_card_usable(card)  # 幂等重绑：同一设备重复绑定，仍校验有效期
        return card, False

    check_card_usable(card)
    card.device = device
    card.status = CardKey.STATUS_BOUND
    card.bound_at = now
    card.save(update_fields=['device', 'status', 'bound_at', 'updated_at'])
    CardLog.objects.create(
        card=card, action=CardLog.ACTION_BIND, source='client',
        operator_name=device.code, detail={'device_code': device.code},
    )
    return card, True


def poll_card(card_key, device_code):
    card = find_card(card_key)
    device_code = (device_code or '').strip()

    if card.status != CardKey.STATUS_BOUND or card.device is None:
        raise ClientApiError(-10, '卡密未绑定设备')
    if card.device.code != device_code:
        raise ClientApiError(-5, '卡密已绑定其他设备')

    check_card_usable(card)

    card.device.last_seen_at = timezone.now()
    card.device.save(update_fields=['last_seen_at', 'updated_at'])

    remaining = None
    if card.end_time:
        remaining = max(0, int((card.end_time - timezone.now()).total_seconds()))
    return card, remaining


def card_brief(card):
    return {
        'card_key': card.key,
        'status': card.effective_status,
        'status_label': CardKey.STATUS_MAP.get(card.effective_status),
        'start_time': card.start_time.strftime('%Y-%m-%d %H:%M:%S') if card.start_time else None,
        'end_time': card.end_time.strftime('%Y-%m-%d %H:%M:%S') if card.end_time else None,
    }
