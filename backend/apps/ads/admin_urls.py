from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.ads.views import AdImageViewSet, AdSlotViewSet

router = SimpleRouter()
router.register('ad-slots', AdSlotViewSet, basename='ad-slot')
router.register('ad-images', AdImageViewSet, basename='ad-image')

urlpatterns = router.urls
