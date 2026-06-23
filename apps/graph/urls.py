from django.urls import path
from . import views

app_name = 'graph'

urlpatterns = [
    path('', views.graph_page, name='page'),
    path('api/graph/', views.graph_data, name='data'),
    path('api/graph/node/<int:node_id>/', views.graph_node, name='node'),
    path('api/graph/link/', views.graph_link, name='link'),
    path('api/graph/link/<int:edge_id>/', views.graph_unlink, name='unlink'),
]
