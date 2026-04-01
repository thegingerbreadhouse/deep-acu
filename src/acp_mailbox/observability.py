from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def make_turn_id() -> str:
    stamp = utc_now().strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{uuid4().hex[:8]}"


def observability_dir(repo_root: Path) -> Path:
    path = repo_root / ".acp" / "state" / "observability"
    path.mkdir(parents=True, exist_ok=True)
    return path


def event_log_path(repo_root: Path, turn_id: str) -> Path:
    return observability_dir(repo_root) / f"{turn_id}.events.jsonl"


def append_event(log_path: Path, event: dict[str, Any]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event) + "\n")


def append_event_from_env(event: dict[str, Any]) -> None:
    raw_path = os.environ.get("DEEPAGENT_OBSERVABILITY_EVENT_LOG")
    if not raw_path:
        return
    payload = {
        "recorded_at": utc_now_iso(),
        **event,
    }
    append_event(Path(raw_path), payload)


@dataclass
class TurnLog:
    repo_root: Path
    turn_id: str
    prompt: str
    source: str = "mailbox"
    request_file: str | None = None
    started_at: str = field(default_factory=utc_now_iso)
    _start_time: float = field(default_factory=time.perf_counter, repr=False)
    session_id: str | None = None
    outgoing_file: str | None = None
    status: str = "started"
    error_type: str | None = None
    error_message: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    reasoning_tokens: int | None = None
    tool_call_count: int = 0
    thought_block_count: int = 0
    usage_metadata: dict[str, Any] | None = None
    response_metadata: dict[str, Any] | None = None
    chunks: list[dict[str, Any]] = field(default_factory=list)
    response_text: str = ""
    prompt_chars: int = field(init=False)

    def __post_init__(self) -> None:
        self.prompt_chars = len(self.prompt)
        self.write()

    @property
    def path(self) -> Path:
        return observability_dir(self.repo_root) / f"{self.turn_id}.json"

    @property
    def events_path(self) -> Path:
        return event_log_path(self.repo_root, self.turn_id)

    def set_session(self, session_id: str) -> None:
        self.session_id = session_id
        self.write()

    def add_chunk(self, text: str) -> None:
        self.chunks.append(
            {
                "index": len(self.chunks),
                "received_at": utc_now_iso(),
                "elapsed_ms": round((time.perf_counter() - self._start_time) * 1000, 3),
                "chars": len(text),
                "text": text,
            }
        )
        self.response_text += text
        self.write()

    def set_outgoing_file(self, outgoing_path: Path) -> None:
        self.outgoing_file = str(outgoing_path)
        self.write()

    def mark_done(self) -> None:
        self.status = "done"
        self.refresh_from_event_log()
        self.write()

    def mark_error(self, exc: Exception) -> None:
        self.status = "error"
        self.error_type = type(exc).__name__
        self.error_message = str(exc)
        self.refresh_from_event_log()
        self.write()

    def refresh_from_event_log(self) -> None:
        if not self.events_path.exists():
            return
        for line in self.events_path.read_text().splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            if event.get("event") != "llm_end":
                continue
            messages = event.get("messages") or []
            if not messages:
                continue
            message = messages[-1]
            usage = message.get("usage_metadata") or {}
            response = message.get("response_metadata") or {}
            self.usage_metadata = usage
            self.response_metadata = response
            self.input_tokens = usage.get("input_tokens")
            self.output_tokens = usage.get("output_tokens")
            self.total_tokens = usage.get("total_tokens")
            output_details = usage.get("output_token_details") or {}
            self.reasoning_tokens = output_details.get("reasoning")
            self.tool_call_count = len(message.get("tool_calls") or [])
            self.thought_block_count = len(message.get("thought_blocks") or [])

    def serialize(self) -> dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "source": self.source,
            "request_file": self.request_file,
            "session_id": self.session_id,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": utc_now_iso() if self.status in {"done", "error"} else None,
            "elapsed_ms": round((time.perf_counter() - self._start_time) * 1000, 3),
            "prompt_chars": self.prompt_chars,
            "response_chars": len(self.response_text),
            "chunk_count": len(self.chunks),
            "outgoing_file": self.outgoing_file,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "tool_call_count": self.tool_call_count,
            "thought_block_count": self.thought_block_count,
            "usage_metadata": self.usage_metadata,
            "response_metadata": self.response_metadata,
            "event_log_file": str(self.events_path),
            "prompt": self.prompt,
            "response_preview": self.response_text[:500],
            "chunks": self.chunks,
        }

    def write(self) -> None:
        self.path.write_text(json.dumps(self.serialize(), indent=2) + "\n")
