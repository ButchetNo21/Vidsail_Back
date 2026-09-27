import re

from rest_framework import serializers

from apps.accounts.models import User
from apps.accounts.permissions import filter_valid_codes

USERNAME_RE = re.compile(r'^[A-Za-z0-9_]{3,32}$')


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=32)
    password = serializers.CharField(max_length=128, write_only=True)


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(min_length=6, max_length=64, write_only=True)
    permissions = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'real_name', 'permissions', 'is_active']

    def validate_username(self, value):
        if not USERNAME_RE.match(value):
            raise serializers.ValidationError('用户名只能包含字母、数字、下划线，长度3-32')
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('用户名已存在')
        return value

    def validate_permissions(self, value):
        return filter_valid_codes(value)

    def create(self, validated_data):
        # 超级管理员只能创建运营账号
        permissions = validated_data.pop('permissions', [])
        return User.objects.create_user(role=User.ROLE_OPERATOR, permissions=permissions, **validated_data)


class UserUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(min_length=6, max_length=64, write_only=True, required=False, allow_null=True)
    permissions = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = User
        fields = ['real_name', 'password', 'permissions', 'is_active']

    def validate_permissions(self, value):
        return filter_valid_codes(value)

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        from apps.core.utils import fmt_dt
        data = {
            'id': instance.pk,
            'username': instance.username,
            'real_name': instance.real_name,
            'permissions': instance.permissions or [],
            'is_active': instance.is_active,
            'last_login_at': fmt_dt(instance.last_login_at),
            'created_at': fmt_dt(instance.created_at),
        }
        return data
