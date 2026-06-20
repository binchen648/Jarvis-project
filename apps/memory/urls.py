from django.urls import path
from . import views

app_name = 'memory'

urlpatterns = [
    path('timeline/', views.timeline_view, name='timeline'),
    path('graph-data/', views.graph_data, name='graph_data'),
    path('log-from-goal/', views.log_from_goal, name='log_from_goal'),
    path('<int:pk>/', views.detail_view, name='detail'),
    path('<int:pk>/send-to-agent/', views.send_to_agent, name='send_to_agent'),
]
