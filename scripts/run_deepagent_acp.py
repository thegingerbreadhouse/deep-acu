from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime
import logging
import os
from pathlib import Path
import sys
import traceback
from uuid import uuid4

from deepagents import create_deep_agent
from deepagents_acp.server import (
    AgentServerACP,
    AgentSessionContext,
    FilesystemBackend,
    run_acp_agent,
)
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI


DEFAULT_MODEL = "gemini-2.5-flash"


def make_attempt_id() -> str:
    stamp = datetime.now(UTC).strftime("%H%M%S")
    return f"{stamp}-{os.getpid()}-{uuid4().hex[:6]}"


def configure_logging(workspace_root: Path) -> tuple[Path, str]:
    log_dir = workspace_root / ".acp" / "state"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_date = datetime.now(UTC).strftime("%Y-%m-%d")
    log_path = log_dir / f"deepagent-acp-{log_date}.log"
    attempt_id = make_attempt_id()
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logging.basicConfig(
        handlers=[file_handler],
        level=logging.INFO,
        force=True,
    )
    logger = logging.getLogger("deepagent_acp")
    logger.info("=" * 80)
    logger.info(
        "ACP launch attempt start attempt_id=%s pid=%s python=%s cwd=%s",
        attempt_id,
        os.getpid(),
        sys.executable,
        Path.cwd(),
    )
    return log_path, attempt_id


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the repo-local DeepAgent ACP server.")
    parser.add_argument(
        "--workspace",
        default=None,
        help="Workspace root. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("DEEPAGENT_MODEL", DEFAULT_MODEL),
        help="Provider-qualified LangChain model string.",
    )
    parser.add_argument(
        "--name",
        default=os.environ.get("DEEPAGENT_NAME", "DeepAgent ACP"),
        help="Agent display name.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=os.environ.get("DEEPAGENT_DEBUG", "").lower() in {"1", "true", "yes"},
        help="Enable DeepAgent debug mode.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Construct the agent and exit without serving ACP.",
    )
    return parser.parse_args()


def resolve_workspace(raw_workspace: str | None) -> Path:
    if raw_workspace:
        return Path(raw_workspace).resolve()
    return Path(__file__).resolve().parents[1]


def build_model(model_name: str, workspace_root: Path) -> ChatGoogleGenerativeAI:
    src_path = workspace_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from acp_mailbox.langchain_observer import LangChainObservabilityHandler

    return ChatGoogleGenerativeAI(
        model=model_name,
        max_retries=2,
        temperature=1.0,
        include_thoughts=True,
        callbacks=[LangChainObservabilityHandler()],
    )


def agent_factory(
    workspace_root: Path,
    model: str,
    name: str,
    debug: bool,
):
    memory_file = workspace_root / "AGENTS.md"

    def build_agent(context: AgentSessionContext):
        session_root = Path(context.cwd or workspace_root).resolve()
        backend = FilesystemBackend(root_dir=session_root, virtual_mode=True)
        return create_deep_agent(
            model=build_model(model, workspace_root),
            name=name,
            debug=debug,
            memory=[str(memory_file)] if memory_file.exists() else None,
            backend=backend,
            checkpointer=InMemorySaver(),
        )

    return build_agent


def install_placeholder_key_for_check(model: str) -> None:
    if not os.environ.get("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = "placeholder-check-key"


def run_check(workspace_root: Path, model: str, name: str, debug: bool) -> int:
    install_placeholder_key_for_check(model)
    build_agent = agent_factory(workspace_root, model, name, debug)
    build_agent(AgentSessionContext(cwd=str(workspace_root), mode="default"))
    logging.info("DeepAgent ACP check passed for workspace=%s model=%s", workspace_root, model)
    print(f"DeepAgent ACP configuration is valid for workspace: {workspace_root}")
    print(f"Model: {model}")
    print(f"Name: {name}")
    return 0


async def serve(server: AgentServerACP, attempt_id: str) -> None:
    loop = asyncio.get_running_loop()
    logger = logging.getLogger("deepagent_acp")

    def handle_async_exception(loop: asyncio.AbstractEventLoop, context: dict[str, object]) -> None:
        message = context.get("message", "Unhandled asyncio exception")
        exception = context.get("exception")
        logger.error("Async runtime error attempt_id=%s message=%s", attempt_id, message)
        if exception:
            logger.error(
                "Async exception traceback attempt_id=%s\n%s",
                attempt_id,
                "".join(traceback.format_exception(type(exception), exception, exception.__traceback__)),
            )
        else:
            logger.error("Async context attempt_id=%s context=%r", attempt_id, context)

    loop.set_exception_handler(handle_async_exception)
    try:
        await run_acp_agent(server)
    except Exception:
        logger.exception("ACP serve loop crashed attempt_id=%s", attempt_id)
        raise
    finally:
        logger.info("ACP launch attempt end attempt_id=%s", attempt_id)


def main() -> int:
    args = parse_args()
    workspace_root = resolve_workspace(args.workspace)
    log_path, attempt_id = configure_logging(workspace_root)
    logging.info(
        "Starting DeepAgent ACP launcher attempt_id=%s workspace=%s log_path=%s",
        attempt_id,
        workspace_root,
        log_path,
    )
    load_dotenv(workspace_root / ".env")
    logging.info("Loaded dotenv attempt_id=%s from=%s", attempt_id, workspace_root / ".env")
    if args.check:
        return run_check(workspace_root, args.model, args.name, args.debug)

    server = AgentServerACP(
        agent_factory(workspace_root, args.model, args.name, args.debug)
    )
    logging.info(
        "Constructed AgentServerACP attempt_id=%s model=%s name=%s debug=%s",
        attempt_id,
        args.model,
        args.name,
        args.debug,
    )
    asyncio.run(serve(server, attempt_id))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        logging.exception("DeepAgent ACP launcher crashed")
        raise
