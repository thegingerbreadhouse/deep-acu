# DeepAgent ACP In VS Code

This repo now contains a runnable DeepAgent ACP integration for VS Code, built around the official Python `deepagents` and `deepagents-acp` packages and the `vscode-acp` extension.

The setup has two layers:

- a real ACP server launcher in `scripts/run_deepagent_acp.py`
- a workspace-mediated mailbox in `.acp/` so DeepAgent and Copilot can hand work to each other without a custom VS Code extension

## Repo layout

- `.vscode/`: VS Code ACP client and interpreter configuration
- `.acp/`: mailbox, artifacts, protocol templates, and watcher state
- `AGENTS.md`: persistent DeepAgent instructions
- `skills/`: DeepAgent mailbox coordination guidance
- `.github/prompts/`: Copilot prompt files for consume/delegate/request flows
- `src/acp_mailbox/`: Python watcher and mailbox helpers
- `scripts/run_deepagent_acp.py`: repo-local ACP launcher
- `docs/`: source notes, empirical validation steps, and implementation constraints

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

5. Optionally run the mailbox watcher from a shell:

```bash
PYTHONPATH=src conda run --no-capture-output -n acp-deepagent-313 python -m acp_mailbox.watcher
```

6. In Copilot Chat, use one of the workspace prompt files:
   - `delegate-to-deepagent`
   - `request-deepagent-context`
   - `consume-deepagent-artifact`

## ACP server behavior

The launcher script uses the installed Python packages directly:

- `deepagents.create_deep_agent(...)`
- `deepagents_acp.server.AgentServerACP`
- `deepagents_acp.server.run_acp_agent(...)`

At runtime it:

- uses the ACP session `cwd` as the file-system root for the DeepAgent backend
- loads repo instructions from `AGENTS.md`
- loads mailbox guidance from `skills/`
- enables checkpointing for conversation continuity
- constructs `ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=1.0, max_retries=2)` from the local `.env`

## Operating model

- DeepAgent is a general-purpose agent. It can gather context, plan, implement, review, or hand work off.
- Copilot is also a general-purpose agent, but it communicates with DeepAgent through workspace artifacts instead of a direct ACP channel.
- Mailbox artifacts are markdown files with frontmatter-like metadata. They are designed to be inspectable by humans and easy for both agents to write.

## Constraints

- No custom VS Code extension in v1.
- No direct ACP notification path between Copilot and DeepAgent.
- No unit tests in this phase. Validation is empirical and end-to-end.

See [`docs/chub-and-source-notes.md`](docs/chub-and-source-notes.md) and [`docs/empirical-validation.md`](docs/empirical-validation.md) for the implementation basis and validation flow.
