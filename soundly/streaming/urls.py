# streaming/urls.py
from django.urls import path
from django.contrib.auth.views import LogoutView
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
    path('play/recommended/<int:song_id>/', views.PlayRecommendedSongsView.as_view(), name='play_recommended'),
    path('play/playlist/<int:playlist_id>/', views.PlayPlaylistSongsView.as_view(), name='play_playlist'),
    path('add-to-playlist/', views.add_to_playlist, name='add_to_playlist'),
    path('register-play/', views.register_play, name='register_play'),
    path('profile/<str:username>/', views.UserProfileView.as_view(), name='user_profile'),
    path('songs/delete/<int:song_id>/', views.DeleteSongView.as_view(), name='delete_song'),
    path('albums/delete/<int:album_id>/', views.DeleteAlbumView.as_view(), name='delete_album'),
    path('update-name/', views.update_name, name='update_name'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),

]