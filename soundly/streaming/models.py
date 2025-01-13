from django.db import models
from django.contrib.auth.models import User
from colorfield.fields import ColorField

from .audio_processing import extract_audio_features

class Song(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='songs')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='songs/')
    release_date = models.DateField(blank=True, null=True) 
    uploaded_at = models.DateTimeField(auto_now_add=True)
    cover_image = models.ImageField(upload_to='song_covers/', blank=True, null=True,default='song_covers/default.png')

    # Características de la canción
    duration_ms = models.PositiveIntegerField(blank=True, null=True)
    danceability = models.FloatField(blank=True, null=True)
    energy = models.FloatField(blank=True, null=True)
    key = models.IntegerField(blank=True, null=True)
    loudness = models.FloatField(blank=True, null=True)
    mode = models.IntegerField(blank=True, null=True)
    speechiness = models.FloatField(blank=True, null=True)
    acousticness = models.FloatField(blank=True, null=True)
    instrumentalness = models.FloatField(blank=True, null=True)
    liveness = models.FloatField(blank=True, null=True)
    valence = models.FloatField(blank=True, null=True)
    tempo = models.FloatField(blank=True, null=True)
    time_signature = models.IntegerField(blank=True, null=True)
    track_genre = models.JSONField(default=list, blank=True)  # Almacena un arreglo de géneros

    def save(self, *args, **kwargs):
        try:
            song_features = extract_audio_features(self.file)
            
            self.duration_ms = song_features["duration_ms"]
            self.tempo = song_features["tempo"]
            self.danceability = song_features["danceability"]
            self.energy = song_features["energy"]
            self.loudness = song_features["loudness"]
            self.acousticness = song_features["acousticness"]
            self.key = song_features["key"]
            self.mode = song_features["mode"]
            self.speechiness = song_features["speechiness"]
            self.instrumentalness = song_features["instrumentalness"]
            self.liveness = song_features["liveness"]
            self.valence = song_features["valence"]
            self.time_signature = song_features["time_signature"]
            self.track_genre = song_features["track_genre"]

        except Exception as e:
            print(f"Error procesando el archivo de audio: {e}")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Album(models.Model):
    title = models.CharField(max_length=200)  
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='album')
    release_date = models.DateField(blank=True, null=True)  # Fecha de lanzamiento
    cover_image = models.ImageField(upload_to='album_covers/', blank=True, null=True, default='song_covers/default.png') 
    songs = models.ManyToManyField(Song, related_name='albums') 
    created_at = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return self.title
    
class Playlist(models.Model):
    name = models.CharField(max_length=200)  # Nombre de la lista de reproducción
    description = models.TextField(blank=True, null=True)  # Descripción opcional
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')  # Usuario que la creó
    songs = models.ManyToManyField(Song, related_name='playlists')  # Relación con las canciones
    color = ColorField(default='#800080')
    created_at = models.DateTimeField(auto_now_add=True)  # Fecha de creación
    updated_at = models.DateTimeField(auto_now=True)  # Fecha de última modificación

    def __str__(self):
        return self.name
    

class LikedSong(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_songs')
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='liked_by')
    liked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'song')  # Evitar duplicados
        verbose_name = 'Liked Song'
        verbose_name_plural = 'Liked Songs'

    def __str__(self):
        return f"{self.user.username} likes {self.song.title}"

class SongHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='song_history')
    song = models.ForeignKey('Song', on_delete=models.CASCADE, related_name='played_by')
    played_at = models.DateTimeField(auto_now_add=True)
    play_count = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'Song History'
        verbose_name_plural = 'Song Histories'
        ordering = ['-played_at']  # Ordenar por la reproducción más reciente

    def __str__(self):
        return f"{self.user.username} played {self.song.title} {self.play_count} times"