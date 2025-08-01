from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from core.views import dashboard_redirect, home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('core/', include('core.urls')),
    path('gym/', include('gym.urls')),
    path('system/', include('system.urls')),
    path('dashboard/', dashboard_redirect, name='dashboard_redirect'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)