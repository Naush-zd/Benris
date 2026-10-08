import platform

import pyttsx3
import speech_recognition as sr


class SpeechService:
    def __init__(self) -> None:
        driver = "sapi5" if platform.system() == "Windows" else None
        try:
            self.engine = pyttsx3.init(driver)
            voices = self.engine.getProperty("voices")
            if voices:
                self.engine.setProperty("voice", voices[0].id)
        except Exception as error:
            self.engine = None
            print(f"Text-to-speech unavailable: {error}")

    def speak(self, text: str) -> None:
        if self.engine is None:
            print(f"Assistant: {text}")
            return
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as error:
            print(f"Text-to-speech error: {error}")

    def listen(self) -> str:
        try:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                print("Listening...")
                recognizer.pause_threshold = 1
                recognizer.energy_threshold = 390
                audio = recognizer.listen(source)

            print("recognizing....")
            query = recognizer.recognize_google(audio, language="en-in")
            print(f"user said : {query}\n")
            return query
        except Exception as error:
            message = "say that again please... or check your microphone or internet connection"
            print(f"{message} ({error})")
            return ""