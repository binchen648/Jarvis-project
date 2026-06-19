from django.urls import path
from . import views

app_name = 'wellness'

urlpatterns = [
    path('suggestions/', views.suggestion_list, name='suggestion_list'),
    path('suggestions/<int:pk>/dismiss/', views.dismiss_suggestion, name='dismiss_suggestion'),
    path('record/', views.record_create, name='record_create'),
]
