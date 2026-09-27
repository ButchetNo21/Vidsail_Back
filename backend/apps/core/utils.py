"""时间格式化等工具。"""
from django.utils import timezone


def fmt_dt(dt):
    if not dt:
        return None
    local = timezone.localtime(dt) if timezone.is_aware(dt) else dt
    return local.strftime('%Y-%m-%d %H:%M:%S')


def now_ts_ms():
    import time
    return int(time.time() * 1000)
