from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import BaseUserManager
from django.db import models

from apps.core.models import BaseModel
from apps.core.utils import fmt_dt


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra):
        if not username:
            raise ValueError('用户名不能为空')
        user = self.model(username=username, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra):
        extra.setdefault('role', User.ROLE_SUPER)
        return self.create_user(username, password, **extra)


class User(AbstractBaseUser, BaseModel):
    ROLE_SUPER = 'super'
    ROLE_OPERATOR = 'operator'
    ROLE_CHOICES = ((ROLE_SUPER, '超级管理员'), (ROLE_OPERATOR, '运营'))

    username = models.CharField(max_length=32, unique=True, verbose_name='用户名')
    real_name = models.CharField(max_length=32, blank=True, default='', verbose_name='姓名')
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default=ROLE_OPERATOR, verbose_name='角色')
    permissions = models.JSONField(default=list, blank=True, verbose_name='权限编码列表')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    last_login_at = models.DateTimeField(null=True, blank=True, verbose_name='最后登录时间')

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []
    objects = UserManager()

    class Meta:
        db_table = 'account_user'
        ordering = ['-id']

    def __str__(self):
        return self.username

    @property
    def is_superuser(self):
        return self.role == self.ROLE_SUPER

    def has_perm(self, code):
        return self.is_superuser or code in (self.permissions or [])

    def to_dict(self):
        return {
            'id': self.pk,
            'username': self.username,
            'real_name': self.real_name,
            'role': self.role,
            'role_label': self.get_role_display(),
            'is_super': self.is_superuser,
            'permissions': self.permissions or [],
            'is_active': self.is_active,
            'last_login_at': fmt_dt(self.last_login_at),
            'created_at': fmt_dt(self.created_at),
        }
