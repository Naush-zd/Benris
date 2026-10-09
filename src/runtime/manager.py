from __future__ import annotations

from collections.abc import Callable

from ..assistant import FallbackAgent
from ..core.events import EventLog
from ..security.policy import PolicyDecision, PolicyEngine
from ..tools import action_sink
from .executor import TaskExecutor
from .session import TaskSession


class TaskManager:
    """Control-plane facade for starting and controlling local agent tasks."""

    def __init__(self, agent: FallbackAgent | None) -> None:
        self.agent = agent
        self.event_log = EventLog()
        self.executor = TaskExecutor(self.event_log)
        self.policy = PolicyEngine()

    def submit(self, prompt: str) -> TaskSession:
        return self.executor.submit(prompt, self._build_task(prompt))

    def _build_task(self, prompt: str) -> Callable[[TaskSession], None]:
        def run(session: TaskSession) -> None:
            session.emit("AGENT_STARTED", "Computer Agent started", agent="computer")
            session.checkpoint()
            if self.agent is None:
                raise RuntimeError("No language model is configured")

            def on_action(action: str, message: str, data: dict) -> None:
                session.emit("ACTION_PERFORMED", message, action=action, **data)

            token = action_sink.set(on_action)
            try:
                session.emit("THINKING", "Agent is deciding what to do")
                response = self.agent.run(prompt)
            finally:
                action_sink.reset(token)
            session.checkpoint()
            content = response.content or "The agent returned no response."
            session.emit("AGENT_RESPONSE", content)

        return run

    def get(self, session_id: str) -> TaskSession | None:
        return self.executor.get(session_id)

    def decide(self, action: str) -> PolicyDecision:
        return self.policy.decide(action)