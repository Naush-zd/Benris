from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..assistant import create_agent
from ..runtime.manager import TaskManager


class TaskRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)


class TaskResponse(BaseModel):
    id: str
    task: str
    state: str


manager = TaskManager(create_agent())


def _task_or_404(session_id: str):
    session = manager.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return session


def _task_response(session) -> TaskResponse:
    return TaskResponse(id=session.id, task=session.task, state=session.state.value)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(title="Benris Control Plane", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("BENRIS_WEB_ORIGIN", "http://localhost:3000")],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/policy/{action:path}")
def policy(action: str) -> dict[str, str]:
    decision = manager.decide(action.replace("/", "."))
    return {
        "action": decision.action,
        "decision": decision.decision.value,
        "reason": decision.reason,
    }


@app.post("/tasks", response_model=TaskResponse, status_code=202)
def create_task(request: TaskRequest) -> TaskResponse:
    return _task_response(manager.submit(request.prompt))


@app.get("/tasks/{session_id}")
def get_task(session_id: str) -> dict[str, Any]:
    session = _task_or_404(session_id)
    return {
        "id": session.id,
        "task": session.task,
        "state": session.state.value,
        "events": [
            event.to_dict()
            for event in session.event_log.snapshot()
            if event.session_id == session.id
        ],
    }


@app.post("/tasks/{session_id}/pause", response_model=TaskResponse)
def pause_task(session_id: str) -> TaskResponse:
    session = _task_or_404(session_id)
    session.pause()
    return _task_response(session)


@app.post("/tasks/{session_id}/resume", response_model=TaskResponse)
def resume_task(session_id: str) -> TaskResponse:
    session = _task_or_404(session_id)
    session.resume()
    return _task_response(session)


@app.post("/tasks/{session_id}/stop", response_model=TaskResponse)
def stop_task(session_id: str) -> TaskResponse:
    session = _task_or_404(session_id)
    session.cancel()
    return _task_response(session)


@app.post("/tasks/{session_id}/approve", response_model=TaskResponse)
def approve_task(session_id: str) -> TaskResponse:
    session = _task_or_404(session_id)
    session.approve()
    return _task_response(session)


@app.post("/tasks/{session_id}/reject", response_model=TaskResponse)
def reject_task(session_id: str) -> TaskResponse:
    session = _task_or_404(session_id)
    session.reject()
    return _task_response(session)


@app.websocket("/ws/events")
async def event_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    subscriber = manager.event_log.subscribe()
    try:
        for event in manager.event_log.snapshot():
            await websocket.send_json(event.to_dict())
        while True:
            event = await asyncio.to_thread(subscriber.get)
            await websocket.send_json(event.to_dict())
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass
    finally:
        manager.event_log.unsubscribe(subscriber)