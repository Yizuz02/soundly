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
    path('discover/', views.RecommendationsView.as_view(), name='discover'),
    path('playlists/', views.PlaylistView.as_view(), name='playlist_list'), 
    path('playlists/<int:pk>/', views.PlaylistView.as_view(), name='playlist_detail'), 
    path('playlist/<int:pk>/delete/', views.PlaylistView.as_view(), name='playlist_delete'),
    path('playlist/<int:pk>/remove-song/<int:song_id>/', views.PlaylistView.as_view(), name='remove_song'),
    path('play/recommended/<int:song_id>/', views.play_recommended_songs, name='play_recommended'),
]