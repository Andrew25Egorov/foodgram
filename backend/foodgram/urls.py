"""Foodgram URL Configuration."""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

from api.urls import urls as api_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(api_urls)),
    path(
        'api/redoc/',
        TemplateView.as_view(template_name='redoc.html'),
        name='redoc',
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)