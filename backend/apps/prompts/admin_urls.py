from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.prompts.views import CategoryViewSet, PromptViewSet, TagViewSet

router = SimpleRouter()
router.register('prompts', PromptViewSet, basename='prompt')
router.register('categories', CategoryViewSet, basename='category')
router.register('tags', TagViewSet, basename='tag')

urlpatterns = router.urls
