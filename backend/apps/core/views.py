"""视图基类与通用工具。"""
from django.utils import timezone
from rest_framework.viewsets import ModelViewSet

from apps.core.permissions import RequirePerm


class PermViewSet(ModelViewSet):
    """
    通过 perm_map 声明每个 action 需要的权限码，如：
        perm_map = {'list': 'card:view', 'create': 'card:edit'}
    未声明的 action 只要求登录。
    """

    perm_map = {}

    def get_permissions(self):
        permissions = super().get_permissions()
        code = self.perm_map.get(self.action)
        if code:
            self.required_perm = code
            permissions.append(RequirePerm())
        return permissions


def apply_ordering(queryset, request, allowed, default):
    """白名单排序，避免任意字段排序。"""
    ordering = request.query_params.get('ordering')
    if ordering:
        field = ordering.lstrip('-')
        if field in allowed:
            return queryset.order_by(ordering)
    return queryset.order_by(*default)


def parse_date_param(value, end_of_day=False):
    """'2026-01-02' -> datetime；end_of_day=True 时返回当天 23:59:59。"""
    if not value:
        return None
    try:
        from datetime import datetime, time
        dt = datetime.strptime(value, '%Y-%m-%d')
        if end_of_day:
            dt = datetime.combine(dt.date(), time.max)
        return timezone.make_aware(dt)
    except (ValueError, TypeError):
        return None
