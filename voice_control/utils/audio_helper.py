"""Audio Helper for voice control system.

Помощник для работы с аудио данными в системе голосового управления
с поддержкой различных форматов, обработки и анализа аудио.
"""

import os
import wave
import struct
import numpy as np
from typing import Optional, Tuple, List, Dict, Any, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import tempfile
import threading
import time

try:
    import librosa
    import soundfile as sf
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False


class AudioFormat(Enum):
    """Поддерживаемые аудио форматы."""
    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"
    OGG = "ogg"
    M4A = "m4a"
    AAC = "aac"


class AudioBackend(Enum):
    """Доступные аудио бэкенды."""
    PYAUDIO = "pyaudio"
    SOUNDDEVICE = "sounddevice"
    WAVE = "wave"


@dataclass
class AudioConfig:
    """Конфигурация аудио."""
    sample_rate: int = 16000
    channels: int = 1
    bit_depth: int = 16
    chunk_size: int = 1024
    format: AudioFormat = AudioFormat.WAV
    backend: Optional[AudioBackend] = None


@dataclass
class AudioInfo:
    """Информация об аудио файле."""
    duration: float
    sample_rate: int
    channels: int
    bit_depth: int
    format: str
    file_size: int
    frames: int


@dataclass
class AudioFeatures:
    """Аудио характеристики."""
    rms_energy: float
    zero_crossing_rate: float
    spectral_centroid: Optional[float] = None
    spectral_rolloff: Optional[float] = None
    mfcc: Optional[np.ndarray] = None
    pitch: Optional[float] = None
    tempo: Optional[float] = None


class AudioHelper:
    """Помощник для работы с аудио данными.
    
    Обеспечивает загрузку, сохранение, конвертацию и анализ
    аудио файлов с поддержкой различных форматов и бэкендов.
    """
    
    def __init__(self, config: Optional[AudioConfig] = None):
        """Инициализация аудио помощника.
        
        Args:
            config: Конфигурация аудио
        """
        self._config = config or AudioConfig()
        self._available_backends = self._detect_backends()
        self._temp_files: List[str] = []
        self._lock = threading.RLock()
        
        # Выбор оптимального бэкенда
        if not self._config.backend:
            self._config.backend = self._select_best_backend()
    
    def _detect_backends(self) -> List[AudioBackend]:
        """Определение доступных аудио бэкендов.
        
        Returns:
            Список доступных бэкендов
        """
        backends = []
        
        if PYAUDIO_AVAILABLE:
            backends.append(AudioBackend.PYAUDIO)
        
        if SOUNDDEVICE_AVAILABLE:
            backends.append(AudioBackend.SOUNDDEVICE)
        
        # Wave всегда доступен
        backends.append(AudioBackend.WAVE)
        
        return backends
    
    def _select_best_backend(self) -> AudioBackend:
        """Выбор оптимального бэкенда.
        
        Returns:
            Оптимальный бэкенд
        """
        # Приоритет: SoundDevice > PyAudio > Wave
        if AudioBackend.SOUNDDEVICE in self._available_backends:
            return AudioBackend.SOUNDDEVICE
        elif AudioBackend.PYAUDIO in self._available_backends:
            return AudioBackend.PYAUDIO
        else:
            return AudioBackend.WAVE
    
    def load_audio(self, file_path: str, 
                   target_sr: Optional[int] = None,
                   mono: bool = True,
                   normalize: bool = True) -> Tuple[np.ndarray, int]:
        """Загрузка аудио файла.
        
        Args:
            file_path: Путь к аудио файлу
            target_sr: Целевая частота дискретизации
            mono: Конвертировать в моно
            normalize: Нормализовать амплитуду
            
        Returns:
            Кортеж (аудио данные, частота дискретизации)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        try:
            # Использование librosa если доступно
            if LIBROSA_AVAILABLE:
                audio_data, sample_rate = librosa.load(
                    file_path,
                    sr=target_sr,
                    mono=mono
                )
                
                if normalize:
                    audio_data = self._normalize_audio(audio_data)
                
                return audio_data, sample_rate
            
            # Fallback на wave для WAV файлов
            elif file_path.lower().endswith('.wav'):
                return self._load_wav_file(file_path, target_sr, mono, normalize)
            
            else:
                raise ValueError(f"Unsupported audio format. Install librosa for extended format support.")
                
        except Exception as e:
            raise RuntimeError(f"Failed to load audio file {file_path}: {str(e)}")
    
    def _load_wav_file(self, file_path: str, 
                       target_sr: Optional[int] = None,
                       mono: bool = True,
                       normalize: bool = True) -> Tuple[np.ndarray, int]:
        """Загрузка WAV файла с помощью wave модуля.
        
        Args:
            file_path: Путь к WAV файлу
            target_sr: Целевая частота дискретизации
            mono: Конвертировать в моно
            normalize: Нормализовать амплитуду
            
        Returns:
            Кортеж (аудио данные, частота дискретизации)
        """
        with wave.open(file_path, 'rb') as wav_file:
            frames = wav_file.getnframes()
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            
            # Чтение аудио данных
            raw_audio = wav_file.readframes(frames)
            
            # Конвертация в numpy array
            if sample_width == 1:
                dtype = np.uint8
                audio_data = np.frombuffer(raw_audio, dtype=dtype)
                audio_data = audio_data.astype(np.float32) / 128.0 - 1.0
            elif sample_width == 2:
                dtype = np.int16
                audio_data = np.frombuffer(raw_audio, dtype=dtype)
                audio_data = audio_data.astype(np.float32) / 32768.0
            elif sample_width == 4:
                dtype = np.int32
                audio_data = np.frombuffer(raw_audio, dtype=dtype)
                audio_data = audio_data.astype(np.float32) / 2147483648.0
            else:
                raise ValueError(f"Unsupported sample width: {sample_width}")
            
            # Обработка многоканального аудио
            if channels > 1:
                audio_data = audio_data.reshape(-1, channels)
                if mono:
                    audio_data = np.mean(audio_data, axis=1)
            
            # Ресемплинг
            if target_sr and target_sr != sample_rate:
                if LIBROSA_AVAILABLE:
                    audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=target_sr)
                    sample_rate = target_sr
                else:
                    # Простой ресемплинг (не рекомендуется для продакшена)
                    ratio = target_sr / sample_rate
                    new_length = int(len(audio_data) * ratio)
                    audio_data = np.interp(
                        np.linspace(0, len(audio_data), new_length),
                        np.arange(len(audio_data)),
                        audio_data
                    )
                    sample_rate = target_sr
            
            # Нормализация
            if normalize:
                audio_data = self._normalize_audio(audio_data)
            
            return audio_data, sample_rate
    
    def save_audio(self, audio_data: np.ndarray, 
                   file_path: str,
                   sample_rate: int,
                   format: Optional[AudioFormat] = None,
                   bit_depth: int = 16) -> None:
        """Сохранение аудио данных в файл.
        
        Args:
            audio_data: Аудио данные
            file_path: Путь для сохранения
            sample_rate: Частота дискретизации
            format: Формат файла
            bit_depth: Битность
        """
        try:
            # Определение формата по расширению файла
            if not format:
                ext = Path(file_path).suffix.lower().lstrip('.')
                format = AudioFormat(ext) if ext in [f.value for f in AudioFormat] else AudioFormat.WAV
            
            # Создание директории если не существует
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Нормализация данных
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Использование soundfile если доступно
            if LIBROSA_AVAILABLE:
                sf.write(file_path, audio_data, sample_rate, subtype=f'PCM_{bit_depth}')
            
            # Fallback на wave для WAV файлов
            elif format == AudioFormat.WAV:
                self._save_wav_file(audio_data, file_path, sample_rate, bit_depth)
            
            else:
                raise ValueError(f"Unsupported format {format.value}. Install librosa for extended format support.")
                
        except Exception as e:
            raise RuntimeError(f"Failed to save audio file {file_path}: {str(e)}")
    
    def _save_wav_file(self, audio_data: np.ndarray, 
                       file_path: str,
                       sample_rate: int,
                       bit_depth: int) -> None:
        """Сохранение WAV файла с помощью wave модуля.
        
        Args:
            audio_data: Аудио данные
            file_path: Путь для сохранения
            sample_rate: Частота дискретизации
            bit_depth: Битность
        """
        # Конвертация в нужный формат
        if bit_depth == 16:
            audio_int = (audio_data * 32767).astype(np.int16)
        elif bit_depth == 24:
            audio_int = (audio_data * 8388607).astype(np.int32)
        elif bit_depth == 32:
            audio_int = (audio_data * 2147483647).astype(np.int32)
        else:
            raise ValueError(f"Unsupported bit depth: {bit_depth}")
        
        with wave.open(file_path, 'wb') as wav_file:
            wav_file.setnchannels(1 if audio_data.ndim == 1 else audio_data.shape[1])
            wav_file.setsampwidth(bit_depth // 8)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_int.tobytes())
    
    def get_audio_info(self, file_path: str) -> AudioInfo:
        """Получение информации об аудио файле.
        
        Args:
            file_path: Путь к аудио файлу
            
        Returns:
            Информация об аудио файле
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        try:
            # Использование librosa если доступно
            if LIBROSA_AVAILABLE:
                info = sf.info(file_path)
                return AudioInfo(
                    duration=info.duration,
                    sample_rate=info.samplerate,
                    channels=info.channels,
                    bit_depth=info.subtype_info.bits_per_sample if hasattr(info.subtype_info, 'bits_per_sample') else 16,
                    format=info.format,
                    file_size=os.path.getsize(file_path),
                    frames=info.frames
                )
            
            # Fallback на wave для WAV файлов
            elif file_path.lower().endswith('.wav'):
                with wave.open(file_path, 'rb') as wav_file:
                    frames = wav_file.getnframes()
                    sample_rate = wav_file.getframerate()
                    channels = wav_file.getnchannels()
                    sample_width = wav_file.getsampwidth()
                    
                    return AudioInfo(
                        duration=frames / sample_rate,
                        sample_rate=sample_rate,
                        channels=channels,
                        bit_depth=sample_width * 8,
                        format="WAV",
                        file_size=os.path.getsize(file_path),
                        frames=frames
                    )
            
            else:
                raise ValueError(f"Unsupported audio format. Install librosa for extended format support.")
                
        except Exception as e:
            raise RuntimeError(f"Failed to get audio info for {file_path}: {str(e)}")
    
    def extract_features(self, audio_data: np.ndarray, sample_rate: int) -> AudioFeatures:
        """Извлечение характеристик из аудио данных.
        
        Args:
            audio_data: Аудио данные
            sample_rate: Частота дискретизации
            
        Returns:
            Аудио характеристики
        """
        try:
            # Базовые характеристики
            rms_energy = np.sqrt(np.mean(audio_data ** 2))
            
            # Zero crossing rate
            zero_crossings = np.where(np.diff(np.sign(audio_data)))[0]
            zcr = len(zero_crossings) / len(audio_data)
            
            features = AudioFeatures(
                rms_energy=float(rms_energy),
                zero_crossing_rate=float(zcr)
            )
            
            # Расширенные характеристики с librosa
            if LIBROSA_AVAILABLE:
                # Спектральные характеристики
                spectral_centroids = librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)[0]
                features.spectral_centroid = float(np.mean(spectral_centroids))
                
                spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_data, sr=sample_rate)[0]
                features.spectral_rolloff = float(np.mean(spectral_rolloff))
                
                # MFCC
                mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
                features.mfcc = np.mean(mfccs, axis=1)
                
                # Pitch (основная частота)
                try:
                    pitches, magnitudes = librosa.piptrack(y=audio_data, sr=sample_rate)
                    pitch_values = []
                    for t in range(pitches.shape[1]):
                        index = magnitudes[:, t].argmax()
                        pitch = pitches[index, t]
                        if pitch > 0:
                            pitch_values.append(pitch)
                    
                    if pitch_values:
                        features.pitch = float(np.median(pitch_values))
                except Exception:
                    pass
                
                # Tempo
                try:
                    tempo, _ = librosa.beat.beat_track(y=audio_data, sr=sample_rate)
                    features.tempo = float(tempo)
                except Exception:
                    pass
            
            return features
            
        except Exception as e:
            raise RuntimeError(f"Failed to extract audio features: {str(e)}")
    
    def convert_format(self, input_path: str, output_path: str, 
                      target_format: AudioFormat,
                      target_sr: Optional[int] = None,
                      target_channels: Optional[int] = None) -> None:
        """Конвертация аудио файла в другой формат.
        
        Args:
            input_path: Путь к исходному файлу
            output_path: Путь к выходному файлу
            target_format: Целевой формат
            target_sr: Целевая частота дискретизации
            target_channels: Количество каналов
        """
        try:
            # Загрузка исходного файла
            audio_data, sample_rate = self.load_audio(input_path)
            
            # Ресемплинг
            if target_sr and target_sr != sample_rate:
                if LIBROSA_AVAILABLE:
                    audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=target_sr)
                    sample_rate = target_sr
            
            # Изменение количества каналов
            if target_channels:
                if target_channels == 1 and audio_data.ndim > 1:
                    audio_data = np.mean(audio_data, axis=1)
                elif target_channels > 1 and audio_data.ndim == 1:
                    audio_data = np.tile(audio_data[:, np.newaxis], (1, target_channels))
            
            # Сохранение в новом формате
            self.save_audio(audio_data, output_path, sample_rate, target_format)
            
        except Exception as e:
            raise RuntimeError(f"Failed to convert audio format: {str(e)}")
    
    def trim_silence(self, audio_data: np.ndarray, 
                    sample_rate: int,
                    threshold: float = 0.01,
                    frame_length: int = 2048,
                    hop_length: int = 512) -> np.ndarray:
        """Обрезка тишины в начале и конце аудио.
        
        Args:
            audio_data: Аудио данные
            sample_rate: Частота дискретизации
            threshold: Порог тишины
            frame_length: Длина фрейма
            hop_length: Шаг между фреймами
            
        Returns:
            Обрезанные аудио данные
        """
        try:
            if LIBROSA_AVAILABLE:
                # Использование librosa для точной обрезки
                trimmed_audio, _ = librosa.effects.trim(
                    audio_data,
                    top_db=20 * np.log10(threshold),
                    frame_length=frame_length,
                    hop_length=hop_length
                )
                return trimmed_audio
            else:
                # Простая обрезка по амплитуде
                start_idx = 0
                end_idx = len(audio_data)
                
                # Поиск начала
                for i in range(len(audio_data)):
                    if abs(audio_data[i]) > threshold:
                        start_idx = i
                        break
                
                # Поиск конца
                for i in range(len(audio_data) - 1, -1, -1):
                    if abs(audio_data[i]) > threshold:
                        end_idx = i + 1
                        break
                
                return audio_data[start_idx:end_idx]
                
        except Exception as e:
            raise RuntimeError(f"Failed to trim silence: {str(e)}")
    
    def _normalize_audio(self, audio_data: np.ndarray, target_level: float = 0.95) -> np.ndarray:
        """Нормализация аудио данных.
        
        Args:
            audio_data: Аудио данные
            target_level: Целевой уровень (0.0 - 1.0)
            
        Returns:
            Нормализованные аудио данные
        """
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            return audio_data * (target_level / max_val)
        return audio_data
    
    def create_temp_file(self, suffix: str = ".wav") -> str:
        """Создание временного аудио файла.
        
        Args:
            suffix: Расширение файла
            
        Returns:
            Путь к временному файлу
        """
        with self._lock:
            temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            self._temp_files.append(temp_path)
            return temp_path
    
    def cleanup_temp_files(self) -> None:
        """Очистка временных файлов."""
        with self._lock:
            for temp_file in self._temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception:
                    pass
            
            self._temp_files.clear()
    
    def get_supported_formats(self) -> List[str]:
        """Получение списка поддерживаемых форматов.
        
        Returns:
            Список поддерживаемых форматов
        """
        if LIBROSA_AVAILABLE:
            return [format.value for format in AudioFormat]
        else:
            return [AudioFormat.WAV.value]
    
    def get_available_backends(self) -> List[str]:
        """Получение списка доступных бэкендов.
        
        Returns:
            Список доступных бэкендов
        """
        return [backend.value for backend in self._available_backends]
    
    def __del__(self):
        """Деструктор для очистки временных файлов."""
        try:
            self.cleanup_temp_files()
        except Exception:
            pass