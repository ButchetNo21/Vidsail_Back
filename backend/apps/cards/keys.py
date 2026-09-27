"""
卡密生成算法（16 位大写字母数字）：

  结构 = [9 位 加密时间戳] + [6 位 随机数] + [1 位 校验位]

  1. 随机数 rand：30 bit；
  2. 加密时间戳：毫秒时间戳(45 bit) XOR HMAC-SHA256(密钥, rand) 前 6 字节(45 bit)，
     不知道服务端密钥就无法从卡密反推生成时间，也无法批量伪造；
  3. 两段用 32 字符安全字母表（剔除 I/L/O/U 防混淆）编码；
  4. 校验位：加权求和 mod 32，可在不查库的情况下快速识别输入错误。
"""
import hashlib
import hmac
import secrets
import time

from django.conf import settings

ALPHABET = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'  # 32 chars
KEY_LENGTH = 16
_TS_BITS = 45
_RAND_BITS = 30


def _encode(num, length):
    chars = []
    for _ in range(length):
        chars.append(ALPHABET[num & 31])
        num >>= 5
    return ''.join(reversed(chars))


def _checksum(body):
    total = sum(ALPHABET.index(c) * (i + 1) for i, c in enumerate(body))
    return ALPHABET[total % 32]


def generate_card_key():
    """生成唯一卡密，密钥碰撞时自动重试。"""
    from apps.cards.models import CardKey

    secret = settings.CLIENT_API_SECRET.encode()
    for _ in range(10):
        rand = secrets.randbits(_RAND_BITS)
        ts = int(time.time() * 1000) & ((1 << _TS_BITS) - 1)
        keystream = hmac.new(secret, rand.to_bytes(4, 'big'), hashlib.sha256).digest()
        enc_ts = ts ^ (int.from_bytes(keystream[:6], 'big') & ((1 << _TS_BITS) - 1))
        body = _encode(enc_ts, 9) + _encode(rand, 6)
        key = body + _checksum(body)
        if not CardKey.all_objects.filter(key=key).exists():
            return key
    raise RuntimeError('卡密生成失败，请重试')


def is_valid_key_format(key):
    """校验卡密格式与校验位（不查库）。"""
    if not isinstance(key, str) or len(key) != KEY_LENGTH:
        return False
    key = key.upper()
    body, check = key[:15], key[15]
    if any(c not in ALPHABET for c in key):
        return False
    return _checksum(body) == check


def normalize_key(key):
    return (key or '').strip().upper()
