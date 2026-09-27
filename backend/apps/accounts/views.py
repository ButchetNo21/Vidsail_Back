import time  # noqa: F401

from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.models import User
from apps.accounts.permissions import PERMISSION_GROUPS
from apps.accounts.serializers import LoginSerializer


class LoginThrottle(ScopedRateThrottle):
    throttle_scope = 'login'


class LoginView(APIView):
    """登录：返回 access/refresh token 与用户信息。"""
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [LoginThrottle]

    def post(self, request):
        ser = LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        username = ser.validated_data['username']
        password = ser.validated_data['password']

        user = User.objects.filter(username=username).first()
        if user is None or not user.check_password(password):
            raise ValidationError('用户名或密码错误')
        if not user.is_active:
            raise PermissionDenied('账号已被禁用，请联系管理员')

        refresh = RefreshToken.for_user(user)
        user.last_login_at = timezone.now()
        user.save(update_fields=['last_login_at'])
        return Response({'token': str(refresh.access_token), 'refresh': str(refresh), 'user': user.to_dict()})


class RefreshView(TokenRefreshView):
    """刷新 access token。"""
    permission_classes = [AllowAny]
    authentication_classes = []


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(request.user.to_dict())


class LogoutView(APIView):
    """登出：将 refresh token 加入黑名单。"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh = request.data.get('refresh')
        if refresh:
            try:
                RefreshToken(refresh).blacklist()
            except Exception:
                pass
        return Response({'detail': 'ok'})


class PermissionListView(APIView):
    """系统全部权限码（创建运营账号时勾选用）。"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(PERMISSION_GROUPS)
