from __future__ import annotations

import threading
import uuid
from enum import StrEnum

from ..core.events import EventLog, RuntimeEvent


class SessionState(StrEnum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskCancelled(Exception):
    """Raised inside a task when a cancellation request is observed."""


class TaskSession:
    def __init__(self, task: str, event_log: EventLog | None = None) -> None:
        self.id = str(uuid.uuid4())
        self.task = task
        self.event_log = event_log or EventLog()
        self._state = SessionState.CREATED
        self._state_lock = threading.Lock()
        self._resume = threading.Event()
        self._resume.set()
        self._cancelled = threading.Event()
        self._approval = threading.Event()
        self._approved: bool | None = None

    @property
    def state(self) -> SessionState:
        with self._state_lock:
            return self._state

    def set_state(self, state: SessionState, message: str) -> None:
        with self._state_lock:
            self._state = state
        self.emit("STATE_CHANGED", message, state=state.value)

    def emit(self, event_type: str, message: str, **data: object) -> None:
        self.event_log.append(RuntimeEvent(self.id, event_type, message, data=dict(data)))

    def pause(self) -> None:
        if self.state in {SessionState.RUNNING, SessionState.WAITING_APPROVAL}:
            self._resume.clear()
            self.set_state(SessionState.PAUSED, "Task paused")

    def resume(self) -> None:
        if self.state == SessionState.PAUSED:
            self._resume.set()
            self.set_state(SessionState.RUNNING, "Task resumed")

    def cancel(self) -> None:
        self._cancelled.set()
        self._resume.set()
        self._approval.set()
        self.set_state(SessionState.CANCELLED, "Task cancellation requested")

    def checkpoint(self) -> None:
        self._resume.wait()
        if self._cancelled.is_set():
            raise TaskCancelled()

    def request_approval(self, action: str, reason: str) -> bool:
        self._approved = None
        self._approval.clear()
        self.set_state(SessionState.WAITING_APPROVAL, f"Approval required: {action}")
        self.emit("APPROVAL_REQUESTED", reason, action=action)
        self._approval.wait()
        if self._cancelled.is_set():
            raise TaskCancelled()
        approved = self._approved is True
        self.set_state(SessionState.RUNNING, "Approval granted" if approved else "Approval rejected")
        return approved

    def approve(self) -> None:
        self._approved = True
        self._approval.set()

    def reject(self) -> None:
        self._approved = False
        self._approval.set()