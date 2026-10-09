from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from queue import Queue
from typing import Any


@dataclass(frozen=True)
class RuntimeEvent:
    session_id: str
    type: str
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


class EventLog:
    """Thread-safe event history with live subscriber queues."""

    def __init__(self) -> None:
        self._events: list[RuntimeEvent] = []
        self._subscribers: list[Queue[RuntimeEvent]] = []
        self._lock = threading.Lock()

    def append(self, event: RuntimeEvent) -> None:
        with self._lock:
            self._events.append(event)
            subscribers = tuple(self._subscribers)
        for subscriber in subscribers:
            subscriber.put(event)

    def snapshot(self) -> list[RuntimeEvent]:
        with self._lock:
            return list(self._events)

    def subscribe(self) -> Queue[RuntimeEvent]:
        subscriber: Queue[RuntimeEvent] = Queue()
        with self._lock:
            self._subscribers.append(subscriber)
        return subscriber

    def unsubscribe(self, subscriber: Queue[RuntimeEvent]) -> None:
        with self._lock:
            if subscriber in self._subscribers:
                self._subscribers.remove(subscriber)