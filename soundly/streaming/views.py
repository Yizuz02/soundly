from datetime import datetime
import os
import shutil
import json

from click import File
from django.http import JsonResponse
from django.views import View
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from django.http import FileResponse, Http404
from django.views.generic import ListView, TemplateView
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .forms import CustomAuthenticationForm, RegistroUsuarioForm, SongUploadForm, AlbumForm, NewSongForm, PlaylistForm
from .models import Song, Album, Song, Playlist
from .recommendations import recommend_songs_with_similarity

def get_unique_file_path(directory, filename):
    base, extension = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    while os.path.exists(os.path.join(directory, new_filename)):
        new_filename = f"{base}_{counter}{extension}"
        counter += 1
    return os.path.join(directory, new_filename)

class IndexView(TemplateView):
    template_name = 'streaming/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtener la hora actual
        hora_actual = datetime.now().hour

        # Determinar el mensaje según la hora
        if 5 <= hora_actual < 12:
            mensaje = "BUENOS DÍAS"
        elif 12 <= hora_actual < 18:
            mensaje = "BUENAS TARDES"
        else:
            mensaje = "BUENAS NOCHES"

        # Verificar si el usuario está autenticado
        context.update({
            'is_authenticated': self.request.user.is_authenticated,
            'user': self.request.user,
            'mensaje': mensaje,
        })

        return context

class LoginView(LoginView):
    template_name = 'streaming/login.html'
    form_class = CustomAuthenticationForm

class UserRegisterView(FormView):
    template_name = 'streaming/register.html'
    form_class = RegistroUsuarioForm
    success_url = reverse_lazy('home') 

    def form_valid(self, form):
        # Crear el usuario
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()

        # Iniciar sesión automáticamente
        login(self.request, user)
        return super().form_valid(form)

class UploadView(TemplateView):
    template_name = 'streaming/upload.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Verificar si el usuario está autenticado
        context.update({
            'is_authenticated': self.request.user.is_authenticated,
            'user': self.request.user
        })

        return context
    
class UploadSongView(LoginRequiredMixin, FormView):
    template_name = 'streaming/upload_song.html'
    form_class = SongUploadForm
    success_url = reverse_lazy('upload')  # Redirige a la vista de canciones del usuario

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Verificar si el usuario está autenticado
        context.update({
            'is_authenticated': self.request.user.is_authenticated,
            'user': self.request.user
        })
        return context

    def form_valid(self, form):
        # Asocia la canción al usuario autenticado
        song = form.save(commit=False)
        song.user = self.request.user

        # Guarda la canción con los datos adicionales
        song.save()
        return super().form_valid(form)
    
class MySongsView(LoginRequiredMixin, ListView):
    model = Song
    template_name = 'streaming/my_songs.html'
    context_object_name = 'songs'

    def get_queryset(self):
        # Filtra las canciones solo del usuario autenticado
        return Song.objects.filter(user=self.request.user)

@require_POST
@csrf_protect
def update_songs(request):
    try:
        data = json.loads(request.body)
        new_songs = data.get('new_songs', [])
        request.session['new_songs'] = new_songs
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class AlbumCreateView(LoginRequiredMixin, FormView):
    template_name = 'streaming/upload_album.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Verificar si el usuario está autenticado
        context.update({
            'is_authenticated': self.request.user.is_authenticated,
            'user': self.request.user
        })
        return context

    def get(self, request, *args, **kwargs):
        # Obtener las nuevas canciones de la sesión
        new_songs = request.session.get('new_songs', [])
        
        # Convertir el objeto a JSON válido
        new_songs_json = json.dumps(new_songs)
        album_form = AlbumForm(user=request.user)
        new_song_form = NewSongForm()
        
        # Obtener las canciones del usuario
        user_songs = Song.objects.filter(user=request.user)
        
        return render(request, self.template_name, {
            'album_form': album_form,
            'new_song_form': new_song_form,
            'new_songs': new_songs_json,
            'user_songs': user_songs,
            'is_authenticated': self.request.user.is_authenticated,
            'user': self.request.user
        })
    

    def post(self, request, *args, **kwargs):
        # Manejar la creación del álbum
        album_form = AlbumForm(request.POST, request.FILES, user=request.user)
        new_song_form = NewSongForm(request.POST, request.FILES)
        
        # Manejar una canción nueva agregada temporalmente
        if 'add_song' in request.POST and new_song_form.is_valid():
            new_song = new_song_form.save(commit=False)
            new_song.user = request.user

            # Guardar temporalmente en la carpeta temp_audio
            temp_file_path = get_unique_file_path(settings.TEMP_AUDIO_DIR, os.path.basename(new_song.file.name))
            with open(temp_file_path, 'wb') as temp_file:
                for chunk in new_song.file.chunks():
                    temp_file.write(chunk)

            # Guardar detalles en sesión
            new_song_dict = {
                'title': new_song.title,
                'file': temp_file_path,
            }
            request.session['new_songs'] = request.session.get('new_songs', []) + [new_song_dict]
            return redirect('upload_album')
        
        # Manejar la creación completa del álbum
        if 'add_album' in request.POST and album_form.is_valid():
            album = album_form.save(commit=False)
            album.user = request.user  # Asegúrate de asignar el usuario al álbum
            album.save()
            
            # Obtener las canciones del tracklist de la sesión
            tracklist_songs = request.session.get('new_songs', [])
            
            # Procesar cada canción en el tracklist
            for song_data in tracklist_songs:
                if 'id' in song_data:
                    # Si es una canción existente, añadirla al álbum
                    try:
                        song = Song.objects.get(id=song_data['id'], user=request.user)
                        album.songs.add(song)
                    except Song.DoesNotExist:
                        continue
                else:
                    # Si es una canción nueva que aún no se ha procesado
                    try:
                        destination_path = get_unique_file_path(settings.SONGS_DIR, os.path.basename(song_data['file']))
                        
                        song = Song.objects.create(
                            title=song_data['title'],
                            release_date=album.release_date,
                            cover_image=album.cover_image,
                            user=request.user
                        )
                        
                        album.songs.add(song)
                        shutil.move(song_data['file'], destination_path)
                        song.file.name = os.path.join('songs', os.path.basename(destination_path))
                        song.save()
                    except Exception as e:
                        print(f"Error al procesar la canción {song_data['title']}: {e}")
                        continue
            
            # Limpiar la sesión
            request.session.pop('new_songs', None)
            return redirect('upload')
        
        return render(request, self.template_name, {
            'album_form': album_form,
            'new_song_form': new_song_form,
            'new_songs': request.session.get('new_songs', []),
            'is_authenticated': self.request.user.is_authenticated,
            'user': self.request.user
        })

class PlaylistView(LoginRequiredMixin, View):
    def get(self, request, pk=None):
        if pk:
            # Obtener una playlist específica
            playlist = get_object_or_404(Playlist, pk=pk, user=request.user)
            return render(request, 'streaming/playlist_detail.html', {
                'playlist': playlist,
                'is_authenticated': self.request.user.is_authenticated,
                'user': self.request.user
            })
        else:
            # Listar todas las playlists del usuario
            playlists = Playlist.objects.filter(user=request.user)
            return render(request, 'streaming/playlist_list.html', {
                'playlists': playlists,
                'is_authenticated': self.request.user.is_authenticated,
                'user': self.request.user
            })

    def post(self, request):
        # Crear una nueva playlist
        form = PlaylistForm(request.POST)
        if form.is_valid():
            new_playlist = form.save(commit=False)
            new_playlist.user = request.user
            new_playlist.save()
            return redirect('playlist_list')  # Cambiar a la vista de la lista después de crear
        return render(request, 'streaming/playlist_form.html', {
            'form': form,
            'is_authenticated': self.request.user.is_authenticated,
            'user': self.request.user
        })

class RecommendationsView(LoginRequiredMixin, ListView):
    template_name = 'streaming/recommendations.html'
    context_object_name = 'recommendations'

    def get_queryset(self):
        """
        Obtiene las recomendaciones para el usuario actual.
        """
        user = self.request.user
        return recommend_songs_with_similarity(user)