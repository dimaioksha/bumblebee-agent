from RealtimeTTS.engines.base_engine import BaseEngine
import torch
import pyaudio
import numpy as np
from typing import Union, Iterator
import io
from pydub.utils import mediainfo
from pydub import AudioSegment
import tempfile
import pyttsx3
import wave
import os
from langdetect import detect


class RussianTTSEngine(BaseEngine):
    def __init__(self, sample_rate=48000, speaker='xenia', put_accent=True, put_yo=True, min_chunk_length=3):
        super().__init__()
        self.sample_rate = sample_rate
        self.speaker = speaker
        self.put_accent = put_accent
        self.put_yo = put_yo
        self.min_chunk_length = min_chunk_length
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.can_consume_generators = True

        # Загрузка модели Silero TTS
        try:
            print("Loading Silero model...")
            self.model, _ = torch.hub.load(
                repo_or_dir='snakers4/silero-models',
                model='silero_tts',
                language='ru',
                speaker='v4_ru'
            )
            self.model.to(self.device)
            print("Silero model loaded successfully.")
            
            with torch.no_grad():
                self.model.apply_tts(
                    text='Тест раз два три',
                    speaker=self.speaker,
                    sample_rate=self.sample_rate,
                    put_accent=self.put_accent,
                    put_yo=self.put_yo
                )
            print("Silero model tested successfully.")
            
        except Exception as e:
            print(f"Failed to load Silero TTS model: {e}")
    
    def post_init(self):
        self.engine_name = "RussianTTSEngine"
    
    def get_stream_info(self):
        return pyaudio.paInt16, 1, self.sample_rate

    def synthesize(self, text: Union[str, Iterator[str]]) -> bool:
        try:
            # Если text является генератором, объединяем его в один текст
            if isinstance(text, Iterator):
                text = ''.join(text)

            # Проверка текста перед синтезом
            if not text:
                print("Text is empty, nothing to synthesize.")
                return False

            print(f"Synthesizing text: '{text}'")

            # Генерация аудио и сохранение в память
            with torch.no_grad():
                audio_tensor = self.model.apply_tts(
                    text=text,
                    speaker=self.speaker,
                    sample_rate=self.sample_rate,
                    put_accent=self.put_accent,
                    put_yo=self.put_yo
                )

            # Normalize audio in torch without converting to numpy
            max_val = torch.max(torch.abs(audio_tensor))
            audio_tensor = (audio_tensor / max_val * 32767).to(torch.int16)

            # Convert audio tensor to bytes directly
            audio_data = audio_tensor.cpu().numpy().tobytes()

            # Помещаем аудио данные в очередь
            self.queue.put(audio_data)

            return True
        except Exception as e:
            print(f"Error during synthesis: {e}")
            return False

    def stop(self):
        """Implement stop functionality if needed."""
        pass

    def shutdown(self):
        """Implement shutdown functionality if needed."""
        pass



SYNTHESIS_FILE = "system_speech_synthesis.wav"
class SystemVoice:
    def __init__(self, name, id):
        self.name = name
        self.id = id

    def __repr__(self):
        return self.name


class AutoSystemEngine(BaseEngine):
    def __init__(self, voice: str = "Zira", print_installed_voices: bool = False):
        """
        Initializes a system realtime text to speech engine object.

        Args:
            voice (str, optional): Default voice name. Defaults to "Zira".
            print_installed_voices (bool, optional): Indicates if the list of installed voices should be printed. Defaults to False.
        """
        self.engine = pyttsx3.init()
        self.default_voice = voice
        self.voice_mapping = {}
        self.initialize_voice_mapping()
        self.set_voice(voice)
        temp_file_path = tempfile.gettempdir()
        self.file_path = os.path.join(temp_file_path, SYNTHESIS_FILE)

        #if print_installed_voices:
            #print(self.get_voices())

    def post_init(self):
        self.engine_name = "system"

    def get_stream_info(self):
        return pyaudio.paInt16, 1, 22050

    def synthesize(self, text: str) -> bool:
        """
        Synthesizes text to audio stream.

        Args:
            text (str): Text to synthesize.
        """
        # Automatically determine language and set the voice
        detected_language = self.detect_language(text)
        self.set_language_voice(detected_language)

        self.engine.save_to_file(text, self.file_path)
        self.engine.runAndWait()

        # Get media info of the file
        info = mediainfo(self.file_path)

        # Check if the file format is AIFF and convert to WAV if necessary
        if info["format_name"] == "aiff":
            audio = AudioSegment.from_file(self.file_path, format="aiff")
            audio.export(self.file_path, format="wav")

        # Now open the WAV file
        with wave.open(self.file_path, "rb") as wf:
            audio_data = wf.readframes(wf.getnframes())
            self.queue.put(audio_data)
            return True

        return False

    def get_voices(self):
        voice_objects = []
        voices = self.engine.getProperty("voices")
        for voice in voices:
            voice_object = SystemVoice(voice.name, voice.id)
            voice_objects.append(voice_object)
        return voice_objects

    def set_voice(self, voice: Union[str, SystemVoice]):
        if isinstance(voice, SystemVoice):
            self.engine.setProperty("voice", voice.id)
        else:
            installed_voices = self.engine.getProperty("voices")
            if voice is not None:
                for installed_voice in installed_voices:
                    if voice in installed_voice.name:
                        self.engine.setProperty("voice", installed_voice.id)

    def set_language_voice(self, language: str):
        """
        Sets the voice based on the detected language.

        Args:
            language (str): Detected language code ('en', 'ru', etc.).
        """
        voice_name = self.voice_mapping.get(language, self.default_voice)
        self.set_voice(voice_name)

    def initialize_voice_mapping(self):
        """
        Maps language codes to installed voice names.
        """
        self.voice_mapping = {
            'en': "Zira",  # Default English voice
            'ru': "Irina"  # Default Russian voice
        }

    def detect_language(self, text: str) -> str:
        """
        Detects the language of the given text.

        Args:
            text (str): Text to analyze.

        Returns:
            str: Detected language code ('en', 'ru', etc.).
        """
        try:
            language = detect(text)
            #print(f"Detected language: {language}")
            if language not in self.voice_mapping:
                return 'ru'
            else:
                return language
        except Exception as e:
            #print(f"Error detecting language: {e}")
            return 'en'

    def set_voice_parameters(self, **voice_parameters):
        for parameter, value in voice_parameters.items():
            self.engine.setProperty(parameter, value)
