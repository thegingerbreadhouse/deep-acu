# DeepAgent ACP MVP

This repo is a lean ACP-backed DeepAgent for VS Code plus a file-based mailbox for Copilot interoperability.

The LLM boundary is a LangChain `BaseChatModel`. The ACP launcher can use any LangChain chat model as long as your configured factory returns a `BaseChatModel` instance.

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

Core packages:

- `deepagents`
- `deepagents-acp`
- `python-dotenv`

Default example provider package:

- `langchain-google-genai`

## Quick start

1. Create and activate a local Python 3.13 environment, then install:

```bash
pip install -r requirements.txt
```

2. Choose your LangChain chat model strategy:
   - easiest path: use the default factory in [model_loader.py](/Users/kateanderson/Documents/Programming/acp/src/acp_mailbox/model_loader.py), which currently builds a Gemini chat model
   - custom path: point `DEEPAGENT_MODEL_FACTORY` at your own `module:function` that returns a LangChain `BaseChatModel`

3. Set your model-specific credentials by creating a local `.env` file from `.env.example` and updating the values for your chosen provider.

4. Install the recommended VS Code extensions:
   - `formulahendry.acp-client`
   - `github.copilot-chat`
   - `ms-python.python`

5. Open this workspace in VS Code.

6. Copy `.vscode/settings.example.json` to a local `.vscode/settings.json` and edit both absolute paths to match your environment:
   - the Python interpreter path
   - the repo-local `scripts/run_deepagent_acp.py` path
   The local `.vscode/settings.json` file is intentionally gitignored.

7. In the ACP Client panel, connect to `DeepAgent-ACP`.

The example settings file launches:

```bash
/absolute/path/to/your/python /absolute/path/to/your/repo/scripts/run_deepagent_acp.py
```

8. Run the mailbox poller from a shell when you want incoming requests to be processed automatically:

```bash
PYTHONPATH=src python -m acp_mailbox.watcher
```

9. Write markdown requests into `.acp/incoming/`. The poller will ask the ACP agent to fulfill them and write the result into `.acp/outgoing/`.

## Sanity checks

Before using VS Code, verify the ACP server directly over stdio:

```bash
python scripts/acp_smoke_test.py
```

Expected result: ACP initializes, a session is created, and the prompt returns `ACP_SMOKE_OK`.

## Model abstraction

- The ACP launcher expects a LangChain `BaseChatModel`, not a provider-specific class.
- Configure the loader with `DEEPAGENT_MODEL_FACTORY=module.path:function_name`.
- The factory function must accept:
  - `workspace_root: Path`
  - `callbacks: list[BaseCallbackHandler]`
- The factory function must return a LangChain `BaseChatModel`.
- The built-in default factory lives in [model_loader.py](/Users/kateanderson/Documents/Programming/acp/src/acp_mailbox/model_loader.py) and uses Gemini only as an example.

## Operating model

- DeepAgent is a general-purpose agent.
- Copilot communicates with DeepAgent only by writing requests to `.acp/incoming/`.
- DeepAgent responses for Copilot are written only to `.acp/outgoing/`.
- The poller watches `.acp/incoming/`, invokes the ACP agent, and writes the response to `.acp/outgoing/`.
- Each mailbox turn also writes observability artifacts to `.acp/state/observability/`:
  - `<turn-id>.json`: turn summary, status, session ID, token counts, reasoning-token counts
  - `<turn-id>.events.jsonl`: raw LangChain model/tool events for that turn
- ACP launcher logs are written per date under `.acp/state/deepagent-acp-YYYY-MM-DD.log`.
- Each launcher attempt is separated by a clear attempt header and attempt ID.

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

This setup depends on a working model provider configuration. If the active `BaseChatModel` fails or the provider is unavailable, the poller writes an `error` response into `.acp/outgoing/` and the ACP launcher details remain in the dated log file under `.acp/state/`.
