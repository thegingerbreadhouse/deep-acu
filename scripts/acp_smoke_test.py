from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from acp import PROTOCOL_VERSION, spawn_agent_process, text_block
from acp.schema import (
    ClientCapabilities,
    CreateTerminalResponse,
    Implementation,
    InitializeResponse,
    KillTerminalResponse,
    ReadTextFileResponse,
    ReleaseTerminalResponse,
    RequestPermissionResponse,
    TerminalOutputResponse,
    WaitForTerminalExitResponse,
    WriteTextFileResponse,
)
from dotenv import load_dotenv


@dataclass
class SmokeClient:
    updates: list[str] = field(default_factory=list)

    def on_connect(self, conn: Any) -> None:
        self.conn = conn

    async def request_permission(self, options, session_id: str, tool_call, **kwargs: Any) -> RequestPermissionResponse:
        if not options:
            return RequestPermissionResponse(outcome={"kind": "cancelled"})
        return RequestPermissionResponse(outcome={"kind": "selected", "option_id": options[0].option_id})

    async def session_update(self, session_id: str, update, **kwargs: Any) -> None:
        self.updates.append(repr(update))
        print(f"[session_update] {update}")

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
        raise RuntimeError("Terminal use is not supported in ACP smoke test")

    async def terminal_output(self, session_id: str, terminal_id: str, **kwargs: Any) -> TerminalOutputResponse:
        raise RuntimeError("Terminal use is not supported in ACP smoke test")

    async def release_terminal(self, session_id: str, terminal_id: str, **kwargs: Any) -> ReleaseTerminalResponse | None:
        return ReleaseTerminalResponse()

    async def wait_for_terminal_exit(self, session_id: str, terminal_id: str, **kwargs: Any) -> WaitForTerminalExitResponse:
        raise RuntimeError("Terminal use is not supported in ACP smoke test")

    async def kill_terminal(self, session_id: str, terminal_id: str, **kwargs: Any) -> KillTerminalResponse | None:
        return KillTerminalResponse()

    async def ext_method(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(f"Unsupported ACP extension method: {method}")

    async def ext_notification(self, method: str, params: dict[str, Any]) -> None:
        print(f"[ext_notification] {method}: {params}")


async def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    load_dotenv(repo_root / ".env")

    env = dict(os.environ)
    client = SmokeClient()

    async with spawn_agent_process(
        client,
        "conda",
        "run",
        "--no-capture-output",
        "-n",
        "acp-deepagent-313",
        "python",
        "scripts/run_deepagent_acp.py",
        cwd=repo_root,
        env=env,
    ) as (conn, process):
        init = await conn.initialize(
            protocol_version=PROTOCOL_VERSION,
            client_capabilities=ClientCapabilities(),
            client_info=Implementation(name="acp-smoke-test", version="0.1.0"),
        )
        print(f"[initialize] {InitializeResponse.model_validate(init)}")

        session = await conn.new_session(cwd=str(repo_root))
        print(f"[new_session] {session}")

        response = await conn.prompt(
            [text_block("Reply with exactly ACP_SMOKE_OK")],
            session_id=session.session_id,
        )
        print(f"[prompt_response] {response}")

        await asyncio.sleep(0.1)

        if process.returncode not in (None, 0):
            raise RuntimeError(f"ACP server exited with code {process.returncode}")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
