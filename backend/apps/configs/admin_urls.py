from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.configs.views import SysConfigViewSet

router = SimpleRouter()
router.register('configs', SysConfigViewSet, basename='sys-config')

urlpatterns = router.urls
