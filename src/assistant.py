from phi.agent import Agent
from phi.model.groq import Groq
from phi.tools.duckduckgo import DuckDuckGo
from phi.tools.python import PythonTools
from PyQt5.QtCore import QThread

from .config import GROQ_API_KEY, GROQ_MODEL
from .weather import get_weather


def create_agent() -> Agent | None:
    if not GROQ_API_KEY:
        return None

    return Agent(
        instructions=[
            "You are Benris like AI assistant. You can help me with my daily tasks.",
            "Give response in a way that it can be passed to a Text-to-Speech engine. Not in markdown format.",
        ],
        tools=[DuckDuckGo(), PythonTools()],
        model=Groq(id=GROQ_MODEL, api_key=GROQ_API_KEY),
        show_tool_calls=True,
        markdown=False,
        debug_mode=True,
    )


class AssistantWorker(QThread):
    def __init__(self, agent: Agent | None, speech_service) -> None:
        super().__init__()
        self.agent = agent
        self.speech_service = speech_service

    def run(self) -> None:
        while True:
            try:
                query = self.speech_service.listen().lower()
                if not query:
                    continue

                if self.agent is None:
                    self.speech_service.speak("GROQ_API_KEY is not configured.")
                    return

                response = self.agent.run(query)
                self.speech_service.speak(response.content or "I could not generate a response.")

                if "weather" in query:
                    self.speech_service.speak("Please tell me the city name.")
                    city = self.speech_service.listen().lower()
                    if city:
                        self.speech_service.speak(get_weather(city))

                if "bye" in query or "chala ja" in query:
                    self.speech_service.speak("goodbye have a nice day")
                    return
            except Exception as error:
                print(f"Assistant worker error: {error}")
                self.speech_service.speak("Something went wrong. Please try again.")