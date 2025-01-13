import io
import json
import os
from typing import List, Tuple
import joblib
import librosa
import numpy as np
from tensorflow import keras
from pydub import AudioSegment
from django.core.files.storage import default_storage

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Obtener el directorio base del archivo actual
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ruta a la carpeta de modelos
KERAS_MODELS_PATH = os.path.join(BASE_DIR, 'keras_models')

class AdvancedEnsembleModel:
    def __init__(self, num_models: int = 5, input_shape: tuple = (498,), num_classes: int = 114):
        self.num_models = num_models
        self.input_shape = input_shape
        self.num_classes = num_classes
        self.models = []
        self.scaler = None
        self.feature_selector = None
        self.meta_model = None
        self.calibrated_model = None
    
    def predict_top_3(self, feature: np.ndarray, genres: List[str]) -> List[Tuple[str, float]]:
        """Realiza predicción usando el ensemble completo y meta-modelo"""
        feature = np.array(feature)
        if len(feature.shape) == 1:
            feature_reshaped = feature.reshape(1, -1)
        else:
            feature_reshaped = feature
        
        # Seleccionar características
        feature_selected = self.feature_selector.transform(feature_reshaped)
        feature_scaled = self.scaler.transform(feature_selected)
        
        # Obtener predicciones de cada modelo base
        all_predictions = []
        for model, feature_indices in self.models:
            model_input = feature_scaled[:, feature_indices]
            predictions = model.predict(model_input, verbose=0)
            all_predictions.append(predictions)
        
        # Combinar predicciones para meta-modelo
        meta_input = np.hstack(all_predictions)
        
        # Obtener predicciones calibradas del meta-modelo
        ensemble_predictions = self.meta_model.predict_proba(meta_input)[0]
        
        # Obtener top 5
        top_3_indices = np.argsort(ensemble_predictions)[-3:][::-1]
        top_3_predictions = [(genres[idx], float(ensemble_predictions[idx]) * 100) 
                           for idx in top_3_indices]
        
        return top_3_predictions

    @classmethod
    def load_genre_model(cls, load_dir: str) -> 'AdvancedEnsembleModel':
        """
        Carga un modelo ensemble previamente entrenado para clasificar generos musicales.
    
        Args:
            load_dir (str): Directorio donde se encuentran los archivos del modelo
                
        Returns:
            AdvancedEnsembleModel: Instancia del modelo cargado
        """
        # Cargar configuración
        config_path = os.path.join(load_dir, 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        # Crear instancia del modelo
        instance = cls(
            num_models=config['num_models'],
            input_shape=tuple(config['input_shape']),
            num_classes=config['num_classes']
        )
            
        # Cargar modelos base
        instance.models = []
        for model_config in config['model_configs']:
            model_path = os.path.join(load_dir, model_config['model_path'])
            model = keras.models.load_model(model_path)
            feature_indices = np.array(model_config['feature_indices'])
            instance.models.append((model, feature_indices))
            
        # Cargar meta-modelo
        meta_model_path = os.path.join(load_dir, 'meta_model.joblib')
        instance.meta_model = joblib.load(meta_model_path)
            
        # Cargar scaler
        scaler_path = os.path.join(load_dir, 'scaler.joblib')
        instance.scaler = joblib.load(scaler_path)
            
        # Cargar selector de características
        feature_selector_path = os.path.join(load_dir, 'feature_selector.joblib')
        instance.feature_selector = joblib.load(feature_selector_path)
            
        print(f"Modelo ensemble cargado exitosamente desde: {load_dir}")
        return instance

def load_audio_file(file_obj):
    """
    Carga un archivo de audio desde un objeto de carga de archivos de Django.
    
    Args:
        file_obj: Objeto de archivo subido en Django
    
    Returns:
        Tupla de array numpy (series de tiempo de audio), frecuencia de muestreo y ruta de archivo temporal
    """
    # Guardar el archivo temporalmente
    temp_path = default_storage.save('temp_audio/' + file_obj.name, file_obj)
    # Obtener la ruta absoluta si estás usando almacenamiento local
    absolute_path = default_storage.path(temp_path)
    
    try:
        # Usar librosa para cargar el archivo de audio
        # Obtener duración en milisegundos
        # Cargar el archivo de audio
        ye, sir = librosa.load(absolute_path)
    
        # Obtener la duración en segundos
        duration_sec = librosa.get_duration(y=ye, sr=sir)
        
        # Convertir la duración a milisegundos
        duration_ms = duration_sec * 1000
        y, sr = librosa.load(absolute_path, offset=20, duration=29)
        return y, sr, temp_path, duration_ms
    except Exception as e:
        print(f"Error al cargar el archivo de audio: {e}")
        # Limpiar archivo temporal si la carga falla
        if default_storage.exists(temp_path):
            default_storage.delete(temp_path)
        raise

def extract_audio_features(file_obj):
    """
    Extrae características de audio de un archivo de música usando librosa.
    
    Args:
        file_obj: Objeto de archivo subido en Django
        
    Returns:
        dict: Diccionario con las características extraídas
    """
    try:
        
        y, sr, temp_path, duration_ms = load_audio_file(file_obj)
        
        # Calcular características de audio
        # Calcular características rítmicas
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        
        # Calcular características espectrales
        rms = librosa.feature.rms(y=y)[0]
        energy = np.mean(rms**2)
        
        # Calcular características armónicas
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        key = np.argmax(np.mean(chroma, axis=1))
        
        # Simular la detección de género (usando modelo previamente entrenado)
        loaded_ensemble = AdvancedEnsembleModel.load_genre_model(
            os.path.join(KERAS_MODELS_PATH, 'modelo_ensemble')
        )
        
        # Proceso de extracción de características para predicción de género
        def get_feature():
            # Extrayendo características MFCC
            mfcc = np.array(librosa.feature.mfcc(y=y, sr=sr))
            mfcc_mean = mfcc.mean(axis=1)
            mfcc_min = mfcc.min(axis=1)
            mfcc_max = mfcc.max(axis=1)
            mfcc_feature = np.concatenate((mfcc_mean, mfcc_min, mfcc_max))

            # Extrayendo características del espectrograma de Mel
            melspectrogram = np.array(librosa.feature.melspectrogram(y=y, sr=sr))
            melspectrogram_mean = melspectrogram.mean(axis=1)
            melspectrogram_min = melspectrogram.min(axis=1)
            melspectrogram_max = melspectrogram.max(axis=1)
            melspectrogram_feature = np.concatenate((melspectrogram_mean, melspectrogram_min, melspectrogram_max))

            # Extrayendo vector de características de chroma
            chroma_feature = np.array(librosa.feature.chroma_stft(y=y, sr=sr))
            chroma_mean = chroma_feature.mean(axis=1)
            chroma_min = chroma_feature.min(axis=1)
            chroma_max = chroma_feature.max(axis=1)
            chroma_feature = np.concatenate((chroma_mean, chroma_min, chroma_max))

            # Extrayendo características de tonnetz
            tonnetz = np.array(librosa.feature.tonnetz(y=y, sr=sr))
            tntz_mean = tonnetz.mean(axis=1)
            tntz_min = tonnetz.min(axis=1)
            tntz_max = tonnetz.max(axis=1)
            tntz_feature = np.concatenate((tntz_mean, tntz_min, tntz_max))
            
            # Concatenar todas las características
            feature = np.concatenate((chroma_feature, melspectrogram_feature, mfcc_feature, tntz_feature))
            return feature
        
        # Obtener predicción de género
        feature = get_feature()
        print("Feature extraida correctamente")
        genres_list = np.load(os.path.join(KERAS_MODELS_PATH, "genres.npy"), allow_pickle=True).tolist()
        predictions = loaded_ensemble.predict_top_3(feature, genres_list)
        generos = [t[0] for t in predictions]
        
        # Características adicionales de espectro
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        
        # Calcular características de voz/música
        speechiness = np.mean(librosa.feature.melspectrogram(y=y, sr=sr))
        acousticness = np.mean(librosa.feature.spectral_contrast(y=y, sr=sr))
        
        # Calcular "liveness" basado en la variabilidad del espectro
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        liveness = np.mean(spectral_bandwidth)
        
        # Calcular "instrumentalness" basado en características espectrales
        instrumentalness = np.mean(librosa.feature.spectral_flatness(y=y))
        
        # Calcular loudness (aproximación)
        loudness = librosa.amplitude_to_db(rms).mean()
        
        # Detectar compás (time signature)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        _, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
        time_signature = 4  # Por defecto 4/4, es difícil detectarlo automáticamente
        
        # Estimar "danceability" basado en el ritmo y la regularidad
        beat_strength = np.mean(onset_env[beats])
        danceability = beat_strength / np.max(onset_env)
        
        # Estimar "valence" basado en características tonales y rítmicas
        harmonic, percussive = librosa.effects.hpss(y)
        valence = np.mean(harmonic**2) / (np.mean(harmonic**2) + np.mean(percussive**2))
        
        # Detectar modo (mayor/menor)
        mode = 1 if np.mean(chroma[0]) > np.mean(chroma[3]) else 0

        # Limpiar archivo temporal
        if default_storage.exists(temp_path):
            default_storage.delete(temp_path)

        # Devolver un diccionario con todas las características extraídas
        return {
            "duration_ms": duration_ms,  # Duración en milisegundos
            "danceability": float(danceability),  # Capacidad de baile
            "energy": float(energy),  # Energía de la canción
            "key": int(key),  # Clave musical
            "loudness": float(loudness),  # Volumen
            "mode": int(mode),  # Modo (mayor/menor)
            "speechiness": float(speechiness),  # Presencia de palabras habladas
            "acousticness": float(acousticness),  # Probabilidad de ser una grabación acústica
            "instrumentalness": float(instrumentalness),  # Probabilidad de ser instrumental
            "liveness": float(liveness),  # Probabilidad de ser una grabación en vivo
            "valence": float(valence),  # Positividad musical
            "tempo": float(tempo),  # Tempo de la canción
            "time_signature": int(time_signature),  # Firma de tiempo
            "track_genre": generos  # Géneros predichos
        }
        
    except Exception as e:
        # Registrar el error y relanzarlo
        print(f"Error al extraer características de audio: {e}")
        raise