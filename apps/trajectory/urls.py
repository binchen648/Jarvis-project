from django.urls import path
from . import views

app_name = 'trajectory'

urlpatterns = [
    path('skills/', views.skill_graph, name='skill_graph'),
    path('paths/', views.path_list, name='path_list'),
    path('paths/<int:pk>/', views.path_detail, name='path_detail'),
    path('nodes/<int:pk>/complete/', views.complete_node, name='complete_node'),
]
