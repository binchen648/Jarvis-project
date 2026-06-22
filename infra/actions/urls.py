from django.urls import path
from . import views

urlpatterns = [
    path('', views.action_list, name='action_list'),
    path('execute/', views.action_execute, name='action_execute'),
]
