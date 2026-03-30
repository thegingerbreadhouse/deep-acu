from __future__ import annotations

import json
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
    chunks: list[dict[str, Any]] = field(default_factory=list)
    response_text: str = ""
    prompt_chars: int = field(init=False)

    def __post_init__(self) -> None:
        self.prompt_chars = len(self.prompt)
        self.write()

    @property
    def path(self) -> Path:
        obs_dir = self.repo_root / ".acp" / "state" / "observability"
        obs_dir.mkdir(parents=True, exist_ok=True)
        return obs_dir / f"{self.turn_id}.json"

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
        self.write()

    def mark_error(self, exc: Exception) -> None:
        self.status = "error"
        self.error_type = type(exc).__name__
        self.error_message = str(exc)
        self.write()

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
            "prompt": self.prompt,
            "response_preview": self.response_text[:500],
            "chunks": self.chunks,
        }

    def write(self) -> None:
        self.path.write_text(json.dumps(self.serialize(), indent=2) + "\n")
