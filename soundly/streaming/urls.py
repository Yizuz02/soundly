# streaming/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('stream/<str:filename>/', views.stream_audio, name='stream_audio'),
]