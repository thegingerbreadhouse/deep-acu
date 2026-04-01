from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from acp import PROTOCOL_VERSION, spawn_agent_process, text_block
from acp.schema import (
    ClientCapabilities,
    CreateTerminalResponse,
    Implementation,
    KillTerminalResponse,
    ReadTextFileResponse,
    ReleaseTerminalResponse,
    RequestPermissionResponse,
    TerminalOutputResponse,
    WaitForTerminalExitResponse,
    WriteTextFileResponse,
)

from .observability import TurnLog, make_turn_id


@dataclass
class CollectingClient:
    turn_log: TurnLog
    chunks: list[str] = field(default_factory=list)

    def on_connect(self, conn: Any) -> None:
        self.conn = conn

    async def request_permission(self, options, session_id: str, tool_call, **kwargs: Any) -> RequestPermissionResponse:
        if not options:
            return RequestPermissionResponse(outcome={"kind": "cancelled"})
        return RequestPermissionResponse(outcome={"kind": "selected", "option_id": options[0].option_id})

    async def session_update(self, session_id: str, update, **kwargs: Any) -> None:
        content = getattr(update, "content", None)
        text = getattr(content, "text", None)
        if text:
            self.chunks.append(text)
            self.turn_log.add_chunk(text)

    async def write_text_file(self, content: str, path: str, session_id: str, **kwargs: Any) -> WriteTextFileResponse | None:
        target = Path(path)
        if not target.is_absolute():
            target = Path.cwd() / target
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        return WriteTextFileResponse()

    async def read_text_file(
        self, path: str, session_id: str, limit: int | None = None, line: int | None = None, **kwargs: Any
    ) -> ReadTextFileResponse:
        target = Path(path)
        if not target.is_absolute():
            target = Path.cwd() / target
        text = target.read_text()
        return ReadTextFileResponse(content=text)

    async def create_terminal(self, command: str, session_id: str, **kwargs: Any) -> CreateTerminalResponse:
        raise RuntimeError("Terminal use is not supported in mailbox polling")

    async def terminal_output(self, session_id: str, terminal_id: str, **kwargs: Any) -> TerminalOutputResponse:
        raise RuntimeError("Terminal use is not supported in mailbox polling")

    async def release_terminal(self, session_id: str, terminal_id: str, **kwargs: Any) -> ReleaseTerminalResponse | None:
        return ReleaseTerminalResponse()

    async def wait_for_terminal_exit(self, session_id: str, terminal_id: str, **kwargs: Any) -> WaitForTerminalExitResponse:
        raise RuntimeError("Terminal use is not supported in mailbox polling")

    async def kill_terminal(self, session_id: str, terminal_id: str, **kwargs: Any) -> KillTerminalResponse | None:
        return KillTerminalResponse()

    async def ext_method(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(f"Unsupported ACP extension method: {method}")

    async def ext_notification(self, method: str, params: dict[str, Any]) -> None:
        return None


async def run_agent_prompt(
    repo_root: Path,
    prompt: str,
    *,
    turn_log: TurnLog | None = None,
    request_file: str | None = None,
) -> tuple[str, TurnLog]:
    env = dict(os.environ)
    active_turn_log = turn_log or TurnLog(
        repo_root=repo_root,
        turn_id=make_turn_id(),
        prompt=prompt,
        request_file=request_file,
    )
    env["DEEPAGENT_TURN_ID"] = active_turn_log.turn_id
    env["DEEPAGENT_OBSERVABILITY_EVENT_LOG"] = str(active_turn_log.events_path)
    client = CollectingClient(turn_log=active_turn_log)
    python_path = os.environ.get("DEEPAGENT_PYTHON", sys.executable)
    script_path = str((repo_root / "scripts" / "run_deepagent_acp.py").resolve())

    try:
        async with spawn_agent_process(
            client,
            python_path,
            script_path,
            cwd=repo_root,
            env=env,
        ) as (conn, process):
            await conn.initialize(
                protocol_version=PROTOCOL_VERSION,
                client_capabilities=ClientCapabilities(),
                client_info=Implementation(name="acp-mailbox-poller", version="0.1.0"),
            )
            session = await conn.new_session(cwd=str(repo_root))
            active_turn_log.set_session(session.session_id)
            await conn.prompt([text_block(prompt)], session_id=session.session_id)
            await asyncio.sleep(0.1)
            if process.returncode not in (None, 0):
                raise RuntimeError(f"ACP server exited with code {process.returncode}")
    except Exception as exc:
        active_turn_log.mark_error(exc)
        raise
    active_turn_log.mark_done()
    return "".join(client.chunks).strip(), active_turn_log


def run_agent_prompt_sync(
    repo_root: Path,
    prompt: str,
    *,
    turn_log: TurnLog | None = None,
    request_file: str | None = None,
) -> tuple[str, TurnLog]:
    return asyncio.run(run_agent_prompt(repo_root, prompt, turn_log=turn_log, request_file=request_file))
