"""通用权限类。"""
from rest_framework.permissions import BasePermission


class RequirePerm(BasePermission):
    """按视图 required_perm 属性校验运营账号权限；超级管理员恒通过。"""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        code = getattr(view, 'required_perm', None)
        if not code:
            return True
        return user.has_perm(code)


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'super')
