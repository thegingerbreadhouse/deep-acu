from __future__ import annotations

import argparse
import asyncio
import logging
import os
from pathlib import Path
import sys

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


def configure_logging(workspace_root: Path) -> None:
    log_dir = workspace_root / ".acp" / "state"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "deepagent-acp.log"
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        force=True,
    )


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


def main() -> int:
    args = parse_args()
    workspace_root = resolve_workspace(args.workspace)
    configure_logging(workspace_root)
    logging.info("Starting DeepAgent ACP launcher in workspace=%s", workspace_root)
    load_dotenv(workspace_root / ".env")
    logging.info("Loaded dotenv from %s", workspace_root / ".env")
    if args.check:
        return run_check(workspace_root, args.model, args.name, args.debug)

    server = AgentServerACP(
        agent_factory(workspace_root, args.model, args.name, args.debug)
    )
    logging.info("Constructed AgentServerACP with model=%s name=%s", args.model, args.name)
    asyncio.run(run_acp_agent(server))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        logging.exception("DeepAgent ACP launcher crashed")
        raise
