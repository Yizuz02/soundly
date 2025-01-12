# streaming/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='home'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.UserRegisterView.as_view(), name='register'),
    path('upload/', views.UploadView.as_view(), name='upload'),
    path('upload-song/', views.UploadSongView.as_view(), name='upload_song'),
    path('upload-album/', views.AlbumCreateView.as_view(), name='upload_album'),
    path('update_songs/', views.update_songs, name='update_songs'),
    path('my-songs/', views.MySongsView.as_view(), name='my_songs'),
    path('discover/', views.RecommendationsView.as_view(), name='discover'),
    path('playlists/', views.PlaylistView.as_view(), name='playlist_list'),  # Lista de playlists
    path('playlists/<int:pk>/', views.PlaylistView.as_view(), name='playlist_detail'),  # Detalle de una playlist
]