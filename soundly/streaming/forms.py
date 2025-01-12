from django.contrib.auth.forms import AuthenticationForm
from django import forms
from django.contrib.auth.models import User
from colorfield.fields import ColorField

from .widgets import ColorWidget
from .models import Album, Song, Playlist

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',  # Clase CSS personalizada
            'placeholder': '',
        }),
        label="Usuario"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',  # Clase CSS personalizada
            'placeholder': '',
        }),
        label="Contraseña"
    )

class RegistroUsuarioForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '',
            'id': 'id_password',
        }),
        label="Contraseña"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '',
            'id': 'id_confirm_password',
        }),
        label="Confirmar Contraseña"
    )

    class Meta:
        model = User
        fields = ['first_name', 'username', 'email', 'password']
        labels = { 
            'first_name': 'Nombre Completo',
            'username': 'Nombre de Usuario',
            'email': 'Correo Electrónico',
            'password': 'Contraseña', 
        }
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '',
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': '',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        
class SongUploadForm(forms.ModelForm):
    class Meta:
        model = Song
        fields = ['title', 'file', 'release_date', 'cover_image']
        labels = { 
            'title': 'Titulo',
            'release_date': 'Fecha de Publicación',
            'cover_image': 'Imagen de Portada',
            'file': 'Archivo de audio', 
        }
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '',
            }),
            'release_date': forms.DateInput(attrs={
                'class': 'form-control',
                'placeholder': '',
                "type": "date"
            }),
            'cover_image': forms.FileInput(attrs={
                'placeholder': '',
                'accept': "image/*",
                'id':"cover-image-input",
            }),
            'file': forms.FileInput(attrs={
                'placeholder': '',
                'accept': "audio/*",
                'id':"file-input",
            }),
        }


class AlbumForm(forms.ModelForm):

    class Meta:
        model = Album
        fields = ['title', 'release_date', 'cover_image']
        labels = { 
            'title': 'Titulo',
            'release_date': 'Fecha de Publicación',
            'cover_image': 'Imagen de Portada',
        }
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '',
            }),
            'release_date': forms.DateInput(attrs={
                'class': 'form-control',
                'placeholder': '',
                "type": "date"
            }),
            'cover_image': forms.FileInput(attrs={
                'placeholder': '',
                'accept': "image/*",
                'id':"cover-image-input",
            })
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')  # Obtener al usuario del contexto
        super().__init__(*args, **kwargs)

        # Filtrar canciones existentes por usuario autenticado
        self.user = user


class NewSongForm(forms.ModelForm):
    class Meta:
        model = Song
        fields = ['title', 'file']
        labels = {
            'title': 'Título Canción',
            'file': 'Archivo de Audio',
        }
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control', 
                'accept': 'audio/*',
                'id' : "file-input",
            }),
        }

class PlaylistForm(forms.ModelForm):
    class Meta:
        model = Playlist
        fields = ['name', 'description', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        color = forms.CharField(widget=ColorWidget())