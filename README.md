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

This repo is configured for the Conda environment:

- name: `acp-deepagent-313`
- python: `3.13`

Installed packages:

- `deepagents`
- `deepagents-acp`
- `langchain-google-genai`

## Quick start

1. Set your provider credentials by creating a local `.env` file from `.env.example` or exporting `GOOGLE_API_KEY` in your shell.

2. Install the recommended VS Code extensions:
   - `formulahendry.acp-client`
   - `github.copilot-chat`
   - `ms-python.python`

3. Open this workspace in VS Code.

4. In the ACP Client panel, connect to `DeepAgent-ACP`.

The workspace already includes `.vscode/settings.json` with an ACP agent entry that launches:

```bash
/opt/homebrew/Caskroom/miniconda/base/envs/acp-deepagent-313/bin/python /Users/kateanderson/Documents/Programming/acp/scripts/run_deepagent_acp.py
```

5. Run the mailbox poller from a shell when you want incoming requests to be processed automatically:

```bash
PYTHONPATH=src /opt/homebrew/Caskroom/miniconda/base/envs/acp-deepagent-313/bin/python -m acp_mailbox.watcher
```

6. Write markdown requests into `.acp/incoming/`. The poller will ask the ACP agent to fulfill them and write the result into `.acp/outgoing/`.

## Sanity checks

Before using VS Code, verify the ACP server directly over stdio:

```bash
/opt/homebrew/Caskroom/miniconda/base/envs/acp-deepagent-313/bin/python scripts/acp_smoke_test.py
```

Expected result: ACP initializes, a session is created, and the prompt returns `ACP_SMOKE_OK`.

## Operating model

- DeepAgent is a general-purpose agent.
- Copilot communicates with DeepAgent only by writing requests to `.acp/incoming/`.
- DeepAgent responses for Copilot are written only to `.acp/outgoing/`.
- The poller watches `.acp/incoming/`, invokes the ACP agent, and writes the response to `.acp/outgoing/`.

## Mailbox sanity test

1. Start the poller:

```bash
PYTHONPATH=src /opt/homebrew/Caskroom/miniconda/base/envs/acp-deepagent-313/bin/python -m acp_mailbox.watcher
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
