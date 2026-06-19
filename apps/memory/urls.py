from django.urls import path
from . import views

app_name = 'memory'

urlpatterns = [
    path('timeline/', views.timeline_view, name='timeline'),
    path('<int:pk>/', views.detail_view, name='detail'),
]
