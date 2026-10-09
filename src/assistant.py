import threading

from phi.agent import Agent
from phi.model.anthropic import Claude
from phi.model.groq import Groq
from phi.tools.duckduckgo import DuckDuckGo
from phi.tools.python import PythonTools
from .config import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_BASE_URL,
    CLAUDE_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
)
from .tools import SystemControlTools
from .weather import get_weather


def _patch_claude_empty_tool_arguments() -> None:
    """phidata omits "arguments" for no-argument tool calls, then KeyErrors reading it back."""
    original = Claude.format_messages

    def format_messages(self, messages):
        for message in messages:
            for call in getattr(message, "tool_calls", None) or []:
                function = call.get("function")
                if isinstance(function, dict):
                    function.setdefault("arguments", "{}")
        return original(self, messages)

    Claude.format_messages = format_messages


_patch_claude_empty_tool_arguments()


def _agent(model) -> Agent:
    return Agent(
        instructions=[
            "You are Benris like AI assistant. You can help me with my daily tasks.",
            "You control this computer, which is a Mac running macOS. Never mention Windows, "
            "Task Manager, or Windows keyboard shortcuts.",
            "You control this computer. When the user asks you to open a site or app, "
            "play or pause music, change the volume, or close something, call the matching "
            "system_control tool and actually do it.",
            "Never reply with instructions describing how the user could do it themselves, "
            "and never claim an action is done unless a tool call reported success.",
            "Use search_the_web when the user wants results on screen, and DuckDuckGo when "
            "they only want the answer spoken back.",
            "After acting, confirm the result in one short sentence.",
            "Give response in a way that it can be passed to a Text-to-Speech engine. Not in markdown format.",
        ],
        tools=[DuckDuckGo(), PythonTools(), SystemControlTools()],
        model=model,
        # Tool calls reach the UI as ACTION_PERFORMED events, so keep them out of spoken text.
        show_tool_calls=False,
        markdown=False,
        debug_mode=True,
    )


class FallbackAgent:
    def __init__(self, primary: Agent | None, fallback: Agent | None) -> None:
        self.primary = primary
        self.fallback = fallback

    def run(self, query: str):
        if self.primary is None and self.fallback is None:
            raise RuntimeError("No language model is configured")

        if self.primary is None:
            return self.fallback.run(query)

        try:
            return self.primary.run(query)
        except Exception as error:
            if self.fallback is None:
                raise
            print(f"Primary model failed; using Claude fallback: {error}", flush=True)
            return self.fallback.run(query)


def create_agent() -> FallbackAgent | None:
    primary = _agent(Groq(id=GROQ_MODEL, api_key=GROQ_API_KEY)) if GROQ_API_KEY else None
    client_params = {"base_url": ANTHROPIC_BASE_URL} if ANTHROPIC_BASE_URL else None
    fallback = (
        _agent(
            Claude(
                id=CLAUDE_MODEL,
                api_key=ANTHROPIC_API_KEY,
                client_params=client_params,
            )
        )
        if ANTHROPIC_API_KEY
        else None
    )
    return FallbackAgent(primary, fallback) if primary or fallback else None


class AssistantWorker(threading.Thread):
    def __init__(self, agent: FallbackAgent | None, speech_service) -> None:
        super().__init__(daemon=True)
        self.agent = agent
        self.speech_service = speech_service

    def run(self) -> None:
        while True:
            try:
                query = self.speech_service.listen().lower()
                if not query:
                    continue

                if self.agent is None:
                    self.speech_service.speak("No language model is configured.")
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


def run_headless() -> None:
    from .speech import SpeechService

    worker = AssistantWorker(create_agent(), SpeechService())
    worker.run()