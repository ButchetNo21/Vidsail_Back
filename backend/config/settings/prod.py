"""
生产配置：DJANGO_SECRET_KEY / 数据库 / CORS 等全部通过环境变量注入。
启动：gunicorn config.wsgi（自动使用本配置）。
"""
import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403

DEBUG = False

if not os.environ.get('DJANGO_SECRET_KEY'):
    raise ImproperlyConfigured('生产环境必须设置环境变量 DJANGO_SECRET_KEY')

ALLOWED_HOSTS = [h for h in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',') if h]
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured('生产环境必须设置环境变量 DJANGO_ALLOWED_HOSTS')

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [o for o in os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',') if o]
