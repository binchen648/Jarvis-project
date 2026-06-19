from django.urls import path
from . import views

app_name = 'goals'

urlpatterns = [
    path('', views.goal_list, name='goal_list'),
    path('create/', views.goal_create, name='goal_create'),
    path('<int:pk>/', views.goal_detail, name='goal_detail'),
    path('<int:pk>/edit/', views.goal_edit, name='goal_edit'),
    path('<int:pk>/status/', views.update_status, name='update_status'),
    path('session/log/', views.log_session, name='log_session'),
]
