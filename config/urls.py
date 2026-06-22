from django.contrib import admin
from django.urls import path, include

from apps.dashboard import views as dashboard_views

urlpatterns = [
    path('health/', include('apps.health.urls')),
    path('api/core-status/', dashboard_views.core_status, name='core_status'),
    path('api/surface/<int:surface_id>/dismiss/', dashboard_views.dismiss_surface, name='dismiss_surface'),
    path('api/dashboard/layout/', dashboard_views.dashboard_layout, name='dashboard_layout'),
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
