from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.cards.admin_views import CardLogViewSet, CardViewSet

router = SimpleRouter()
router.register('cards', CardViewSet, basename='card')
router.register('card-logs', CardLogViewSet, basename='card-log')

urlpatterns = router.urls
