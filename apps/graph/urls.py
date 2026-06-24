from django.urls import path
from . import views

app_name = 'graph'

urlpatterns = [
    path('', views.graph_page, name='page'),
    path('api/graph/', views.graph_data, name='data'),
    path('api/graph/search/', views.graph_search, name='search'),
    path('api/graph/node/', views.graph_node_create, name='node_create'),
    path('api/graph/node/<int:node_id>/', views.graph_node, name='node'),
    path('api/graph/node/<int:node_id>/suggestions/', views.graph_node_suggestions, name='node_suggestions'),
    path('api/graph/link/', views.graph_link, name='link'),
    path('api/graph/link/<int:edge_id>/', views.graph_link_note_update, name='link_update'),
    path('api/graph/link/<int:edge_id>/note/', views.graph_link_note, name='link_note'),
    path('api/graph/link/<int:edge_id>/delete/', views.graph_unlink, name='unlink'),
]
