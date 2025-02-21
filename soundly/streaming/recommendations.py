import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
from .models import Song, SongHistory, LikedSong

def get_user_preferences(user):
    """
    Obtiene las preferencias del usuario basándose en su historial y canciones gustadas.
    Devuelve géneros más escuchados y canciones favoritas.
    """
    # Obtener canciones reproducidas por el usuario
    history = SongHistory.objects.filter(user=user).select_related('song')
    played_songs = [entry.song for entry in history]

    # Obtener canciones marcadas como gustadas por el usuario
    liked_songs = LikedSong.objects.filter(user=user).select_related('song')
    liked_songs_list = [liked_song.song for liked_song in liked_songs]

    # Combinar canciones del historial y canciones gustadas
    all_songs = played_songs + liked_songs_list

    # Contar géneros de las canciones
    genre_counter = Counter(song.track_genre[0] for song in all_songs)

    # Encontrar las canciones más reproducidas o gustadas
    most_played_or_liked = Counter(all_songs).most_common(10)

    return {
        'top_genres': genre_counter.most_common(3),  # Los 3 géneros principales
        'most_played_or_liked': [song for song, _ in most_played_or_liked]
    }

def get_song_features(song):
    """
    Devuelve un vector de características de la canción.
    """
    return np.array([
        song.danceability, song.energy, song.key, song.loudness,
        song.mode, song.speechiness, song.acousticness,
        song.instrumentalness, song.liveness, song.valence, song.tempo
    ])

def recommend_songs_with_similarity(user):
    """
    Genera recomendaciones basadas en la similitud de las características de las canciones,
    incluyendo información sobre los álbumes a los que pertenecen.
    """
    # Obtener las preferencias del usuario
    preferences = get_user_preferences(user)
    most_played_songs = preferences.get('most_played_or_liked', [])

    if not most_played_songs:
        return []

    # Vectorizar características de las canciones reproducidas
    played_features = np.array([get_song_features(song) for song in most_played_songs])

    # Obtener todas las canciones excluyendo las ya reproducidas o favoritas
    all_songs = Song.objects.exclude(id__in=[song.id for song in most_played_songs])

    if not all_songs.exists():
        return []

    # Vectorizar características de todas las canciones disponibles
    all_features = np.array([get_song_features(song) for song in all_songs])

    # Calcular similitud coseno
    similarities = cosine_similarity(played_features, all_features)

    # Promediar similitudes y ordenar por las más altas
    similarity_scores = similarities.mean(axis=0)
    recommended_indices = np.argsort(-similarity_scores)[:10]

    # Seleccionar las canciones recomendadas
    recommendations = [all_songs[int(i)] for i in recommended_indices]

    # Agregar álbumes relacionados a las canciones recomendadas
    recommendations_with_albums = [
        {'song': song, 'albums': song.albums.all()} for song in recommendations
    ]

    return recommendations_with_albums
