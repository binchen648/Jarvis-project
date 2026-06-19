from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('health/', include('apps.health.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('apps.dashboard.urls')),
    path('', include('apps.accounts.urls')),
    path('content/', include('apps.content.urls')),
    path('goals/', include('apps.goals.urls')),
    path('wellness/', include('apps.wellness.urls')),
    path('trajectory/', include('apps.trajectory.urls')),
    path('memory/', include('apps.memory.urls')),
    path('chat/', include('apps.chat.urls')),
]
