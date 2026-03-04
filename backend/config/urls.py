from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('apps.users.urls')),
    path('api/textbooks/', include('apps.textbooks.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/messages/', include('apps.messaging.urls')),
    path('api/reviews/', include('apps.reviews.urls')),
    path('api/statistics/', include('apps.statistics.urls')),
    path('api/recommendations/', include('apps.recommendations.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
