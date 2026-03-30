# DeepAgent ACP MVP

This repo is a lean ACP-backed DeepAgent for VS Code plus a file-based mailbox for Copilot interoperability.

## Repo layout

- `.vscode/`: ACP client launch config for VS Code
- `.acp/`: mailbox directories and runtime state
- `AGENTS.md`: persistent agent instructions
- `scripts/run_deepagent_acp.py`: ACP server launcher
- `scripts/acp_smoke_test.py`: direct stdio sanity check
- `src/acp_mailbox/watcher.py`: poll `.acp/incoming/` and write `.acp/outgoing/`
- `src/acp_mailbox/acp_runner.py`: invoke the ACP agent from the poller

## Dependencies

Use a local Python 3.13 environment. Conda is the expected setup, but the repo no longer assumes a machine-specific environment name or interpreter path.

Installed packages:

- `deepagents`
- `deepagents-acp`
- `langchain-google-genai`

## Quick start

1. Create and activate a local Python 3.13 environment, then install:

```bash
pip install -r requirements.txt
```

2. Set your provider credentials by creating a local `.env` file from `.env.example` or exporting `GOOGLE_API_KEY` in your shell.

3. Install the recommended VS Code extensions:
   - `formulahendry.acp-client`
   - `github.copilot-chat`
   - `ms-python.python`

4. Open this workspace in VS Code.

5. Copy `.vscode/settings.example.json` to a local `.vscode/settings.json` and edit the Python path to match your environment.
   The local `.vscode/settings.json` file is intentionally gitignored.

6. In the ACP Client panel, connect to `DeepAgent-ACP`.

The example settings file launches:

```bash
/absolute/path/to/your/python ${workspaceFolder}/scripts/run_deepagent_acp.py
```

7. Run the mailbox poller from a shell when you want incoming requests to be processed automatically:

```bash
PYTHONPATH=src python -m acp_mailbox.watcher
```

8. Write markdown requests into `.acp/incoming/`. The poller will ask the ACP agent to fulfill them and write the result into `.acp/outgoing/`.

## Sanity checks

Before using VS Code, verify the ACP server directly over stdio:

```bash
python scripts/acp_smoke_test.py
```

Expected result: ACP initializes, a session is created, and the prompt returns `ACP_SMOKE_OK`.

## Operating model

- DeepAgent is a general-purpose agent.
- Copilot communicates with DeepAgent only by writing requests to `.acp/incoming/`.
- DeepAgent responses for Copilot are written only to `.acp/outgoing/`.
- The poller watches `.acp/incoming/`, invokes the ACP agent, and writes the response to `.acp/outgoing/`.
- Each mailbox turn also writes a per-turn observability record to `.acp/state/observability/`.

## Mailbox sanity test

1. Start the poller:

```bash
PYTHONPATH=src python -m acp_mailbox.watcher
```

2. Create an incoming request:

```text
from: copilot
to: deepagent
---

What are the contents of the .gitignore?
```

3. Confirm the poller writes a response file in `.acp/outgoing/`.

## Constraints

- No custom VS Code extension in v1.
- No direct ACP notification path between Copilot and DeepAgent.
- No unit tests in this phase. Validation is empirical and end-to-end.

## Lean scope

This project intentionally contains only:

- a DeepAgent ACP launcher for VS Code
- a stdio ACP smoke test
- an incoming/outgoing mailbox poller

It does not include custom VS Code extensions, MCP orchestration, terminal tooling, or extra prompt scaffolding.

## Operational note

This setup depends on a working Gemini API key and available quota. If Gemini returns a quota or provider error, the poller writes an `error` response into `.acp/outgoing/` and the ACP launcher details remain in `.acp/state/deepagent-acp.log`.
