from __future__ import annotations

import threading
from collections.abc import Callable

from ..core.events import EventLog
from .session import SessionState, TaskCancelled, TaskSession


Task = Callable[[TaskSession], None]


class TaskExecutor:
    def __init__(self, event_log: EventLog | None = None) -> None:
        self.event_log = event_log or EventLog()
        self._sessions: dict[str, TaskSession] = {}
        self._lock = threading.Lock()

    def submit(self, task_name: str, task: Task) -> TaskSession:
        session = TaskSession(task_name, self.event_log)
        with self._lock:
            self._sessions[session.id] = session

        thread = threading.Thread(target=self._run, args=(session, task), daemon=True)
        thread.start()
        return session

    def get(self, session_id: str) -> TaskSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def _run(self, session: TaskSession, task: Task) -> None:
        session.set_state(SessionState.RUNNING, f"Task started: {session.task}")
        session.emit("TASK_STARTED", session.task)
        try:
            task(session)
        except TaskCancelled:
            session.set_state(SessionState.CANCELLED, "Task cancelled")
        except Exception as error:
            session.set_state(SessionState.FAILED, "Task failed")
            session.emit("TASK_FAILED", str(error), error_type=type(error).__name__)
        else:
            session.set_state(SessionState.COMPLETED, "Task completed")
            session.emit("TASK_COMPLETED", session.task)