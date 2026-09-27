from django.conf import settings
from django.contrib.staticfiles.views import serve as serve_static
from django.urls import include, path
from django.views.static import serve as serve_media

admin_api = [
    path('', include('apps.accounts.admin_urls')),
    path('', include('apps.cards.admin_urls')),
    path('', include('apps.prompts.admin_urls')),
    path('', include('apps.ads.admin_urls')),
    path('', include('apps.configs.admin_urls')),
    path('', include('apps.dashboard.admin_urls')),
]

urlpatterns = [
    path('api/auth/', include('apps.accounts.urls')),
    path('api/client/', include('apps.cards.client_urls')),
    path('api/admin/', include(admin_api)),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path('static/<path:path>', serve_static)]
