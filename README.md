# DeepAgent ACP In VS Code

This repo now contains a runnable DeepAgent ACP integration for VS Code, built around the official Python `deepagents` and `deepagents-acp` packages and the `vscode-acp` extension.

The setup has two layers:

- a real ACP server launcher in `scripts/run_deepagent_acp.py`
- a simplified workspace mailbox in `.acp/incoming` and `.acp/outgoing`

## Repo layout

- `.vscode/`: VS Code ACP client and interpreter configuration
- `.acp/`: incoming/outgoing mailbox and runtime state
- `AGENTS.md`: persistent DeepAgent instructions
- `src/acp_mailbox/`: Python watcher and mailbox helpers
- `scripts/`: ACP launcher and ACP smoke test

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

4. In the ACP Client panel, connect to `DeepAgent ACP`.

The workspace already includes `.vscode/settings.json` with an ACP agent entry that launches:

```bash
conda run --no-capture-output -n acp-deepagent-313 python scripts/run_deepagent_acp.py
```

5. Run the mailbox poller from a shell when you want incoming requests to be processed automatically:

```bash
PYTHONPATH=src conda run --no-capture-output -n acp-deepagent-313 python -m acp_mailbox.watcher
```

6. Write markdown requests into `.acp/incoming/`. The poller will ask the ACP agent to fulfill them and will write the answer into `.acp/outgoing/`.

## ACP smoke test

Before using VS Code, you can verify the ACP server directly over stdio:

```bash
conda run --no-capture-output -n acp-deepagent-313 python scripts/acp_smoke_test.py
```

Expected result:

- ACP initialize succeeds
- a new session is created
- the prompt returns `ACP_SMOKE_OK`
- the prompt response ends with `stop_reason='end_turn'`

## ACP server behavior

The launcher script uses the installed Python packages directly:

- `deepagents.create_deep_agent(...)`
- `deepagents_acp.server.AgentServerACP`
- `deepagents_acp.server.run_acp_agent(...)`

At runtime it:

- uses the ACP session `cwd` as the file-system root for the DeepAgent backend
- loads repo instructions from `AGENTS.md`
- enables checkpointing for conversation continuity
- constructs `ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=1.0, max_retries=2)` from the local `.env`

## Operating model

- DeepAgent is a general-purpose agent.
- Copilot communicates with DeepAgent only by writing requests to `.acp/incoming/`.
- DeepAgent responses for Copilot are written only to `.acp/outgoing/`.
- The poller watches `.acp/incoming/`, invokes the ACP agent, and writes the response to `.acp/outgoing/`.

## Constraints

- No custom VS Code extension in v1.
- No direct ACP notification path between Copilot and DeepAgent.
- No unit tests in this phase. Validation is empirical and end-to-end.

## Minimal test

1. Start the poller:

```bash
PYTHONPATH=src /opt/homebrew/Caskroom/miniconda/base/envs/acp-deepagent-313/bin/python -m acp_mailbox.watcher
```

2. Create an incoming request:

```bash
cat > .acp/incoming/gitignore-test.md <<'EOF'
from: copilot
to: deepagent
---

what are the contents of the .gitignore?
EOF
```

3. Confirm the poller writes a response file in `.acp/outgoing/` containing the actual `.gitignore` contents.
