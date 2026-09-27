from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.routers import SimpleRouter
from rest_framework.viewsets import GenericViewSet

from apps.accounts.models import User
from apps.accounts.serializers import UserCreateSerializer, UserUpdateSerializer
from apps.core.exceptions import ValidationError
from apps.core.permissions import IsSuperAdmin


class UserViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                  mixins.UpdateModelMixin, mixins.DestroyModelMixin, GenericViewSet):
    """账号管理（仅超级管理员）：创建/编辑运营账号、启停、重置密码。"""
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    queryset = User.objects.filter(role=User.ROLE_OPERATOR).order_by('-id')
    serializer_class = UserCreateSerializer

    def get_serializer_class(self):
        if self.action in ('update', 'partial_update', 'reset_password'):
            return UserUpdateSerializer
        return UserCreateSerializer

    def get_throttles(self):
        return []

    def perform_destroy(self, instance):
        # 账号不做物理删除，停用即可
        instance.is_active = False
        instance.save(update_fields=['is_active', 'updated_at'])

    def perform_update(self, serializer):
        if 'is_active' in serializer.validated_data and serializer.instance.pk == self.request.user.pk:
            raise ValidationError('不能停用当前登录账号')
        serializer.save()

    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        user = self.get_object()
        password = (request.data.get('password') or '').strip()
        if len(password) < 6:
            raise ValidationError('密码长度至少6位')
        user.set_password(password)
        user.save(update_fields=['password', 'updated_at'])
        return Response({'detail': 'ok'}, status=status.HTTP_200_OK)


router = SimpleRouter()
router.register('users', UserViewSet, basename='user')

urlpatterns = router.urls
