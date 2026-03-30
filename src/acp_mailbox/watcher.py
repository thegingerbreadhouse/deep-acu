from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path


WATCH_DIRS = (".acp/tasks", ".acp/messages", ".acp/artifacts")
STATE_PATH = Path(".acp/state/watcher-state.json")


@dataclass(frozen=True)
class MailboxEvent:
    path: Path
    digest: str


def compute_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_state(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_state(path: Path, state: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def iter_markdown_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for rel_dir in WATCH_DIRS:
        watch_dir = root / rel_dir
        if not watch_dir.exists():
            continue
        files.extend(sorted(watch_dir.glob("*.md")))
    return files


def detect_events(root: Path, state: dict[str, str]) -> tuple[list[MailboxEvent], dict[str, str]]:
    next_state = dict(state)
    events: list[MailboxEvent] = []
    for path in iter_markdown_files(root):
        digest = compute_digest(path)
        rel_path = str(path.relative_to(root))
        if state.get(rel_path) != digest:
            events.append(MailboxEvent(path=path, digest=digest))
        next_state[rel_path] = digest
    return events, next_state


def print_event(root: Path, event: MailboxEvent) -> None:
    rel_path = event.path.relative_to(root)
    header = event.path.read_text().split("---", 1)[0].strip()
    print(f"[mailbox] update detected: {rel_path}")
    if header:
        print(header)
    print()


def run_once(root: Path, state_path: Path) -> int:
    state = load_state(state_path)
    events, next_state = detect_events(root, state)
    for event in events:
        print_event(root, event)
    save_state(state_path, next_state)
    return 0


def watch(root: Path, state_path: Path, interval: float) -> int:
    while True:
        run_once(root, state_path)
        time.sleep(interval)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Watch the ACP workspace mailbox.")
    parser.add_argument("--root", default=".", help="Repository root to watch.")
    parser.add_argument(
        "--state-file",
        default=str(STATE_PATH),
        help="Path to the watcher state file.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Polling interval in seconds.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Scan once and exit.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    state_path = (root / args.state_file).resolve()
    if args.once:
        return run_once(root, state_path)
    return watch(root, state_path, args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
