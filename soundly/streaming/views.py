from django.shortcuts import render
from django.conf import settings
import os
from django.http import FileResponse, Http404

def stream_audio(request, filename):
    filepath = os.path.join(settings.MEDIA_ROOT, 'music', filename)
    if os.path.exists(filepath):
        return FileResponse(open(filepath, 'rb'), content_type='audio/mpeg')
    else:
        raise Http404("Archivo de audio no encontrado")
    
def index(request):
    return render(request, 'streaming/index.html')