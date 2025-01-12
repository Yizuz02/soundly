from django.contrib import admin
from .models import Song, Album, Playlist, LikedSong, SongHistory

admin.site.register(Song)
admin.site.register(Album)
admin.site.register(Playlist)
admin.site.register(LikedSong)
admin.site.register(SongHistory)
