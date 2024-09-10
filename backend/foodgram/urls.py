"""Foodgram URL Configuration."""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

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
