from django.urls import path
from . import views

app_name = 'content'

urlpatterns = [
    path('feed/', views.feed, name='feed'),
    path('submit/', views.submit_url, name='submit_url'),
    path('submitted/', views.submitted_list, name='submitted_list'),
    path('<int:content_id>/', views.detail, name='detail'),
    path('<int:content_id>/interact/', views.interact, name='interact'),
]
