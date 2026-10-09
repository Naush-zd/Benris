import os

import pyttsx3
import pyaudio
import speech_recognition as sr


class SpeechService:
    def __init__(self) -> None:
        self.microphone_index = self._read_index("BENRIS_MICROPHONE_INDEX")
        try:
            self.engine = pyttsx3.init()
            voices = self.engine.getProperty("voices")
            if voices:
                voice_index = self._read_index("BENRIS_VOICE_INDEX")
                if voice_index is None:
                    voice_index = self._preferred_voice_index(voices)
                voice_index = min(voice_index, len(voices) - 1)
                self.engine.setProperty("voice", voices[voice_index].id)
                print(f"VOICE: {voice_index} - {voices[voice_index].name}", flush=True)
        except Exception as error:
            self.engine = None
            print(f"Text-to-speech unavailable: {error}", flush=True)

    @staticmethod
    def _read_index(variable: str) -> int | None:
        value = os.getenv(variable)
        if value is None:
            return None
        try:
            index = int(value)
            return index if index >= 0 else None
        except ValueError:
            print(f"Ignoring invalid {variable}: {value}", flush=True)
            return None

    @staticmethod
    def _preferred_voice_index(voices) -> int:
        preferred_names = ("Samantha", "Alex", "Karen", "Daniel", "Ava")
        for name in preferred_names:
            for index, voice in enumerate(voices):
                if name.lower() in voice.name.lower():
                    return index
        return 0

    def _microphone_name(self) -> str:
        try:
            audio = pyaudio.PyAudio()
            if self.microphone_index is None:
                info = audio.get_default_input_device_info()
                audio.terminate()
                return f"default [{int(info['index'])}] - {info['name']}"
            names = sr.Microphone.list_microphone_names()
            audio.terminate()
            if self.microphone_index < len(names):
                return f"[{self.microphone_index}] - {names[self.microphone_index]}"
        except Exception as error:
            print(f"Unable to identify microphone: {error}", flush=True)
        return "unknown"

    def speak(self, text: str) -> None:
        if self.engine is None:
            print(f"Assistant: {text}", flush=True)
            return
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as error:
            print(f"Text-to-speech error: {error}", flush=True)

    def listen(self) -> str:
        try:
            recognizer = sr.Recognizer()
            with sr.Microphone(device_index=self.microphone_index) as source:
                print(f"MICROPHONE: {self._microphone_name()}", flush=True)
                print("Listening...", flush=True)
                recognizer.pause_threshold = 1
                recognizer.energy_threshold = 390
                audio = recognizer.listen(source)

            print("recognizing....", flush=True)
            query = recognizer.recognize_google(audio, language="en-in")
            print(f"TRANSCRIPT: {query}", flush=True)
            return query
        except Exception as error:
            message = "say that again please... or check your microphone or internet connection"
            print(f"{message} ({error})", flush=True)
            return ""