# Empirical Validation

This repo intentionally avoids unit tests for the first phase. Validation should happen in the actual shell + VS Code workflow.

## Validation flow

1. Start the watcher:

```bash
PYTHONPATH=src python -m acp_mailbox.watcher
```

Optional ACP-only validation before opening VS Code:

```bash
conda run --no-capture-output -n acp-deepagent-313 python scripts/acp_smoke_test.py
```

Expected outcome:
- ACP handshake succeeds over stdio
- the server streams `ACP_SMOKE_OK`

2. Start DeepAgent via `deepagents-acp` in `vscode-acp`.

In VS Code:

- install `ACP Client` and `GitHub Copilot Chat`
- open the ACP Client panel
- connect to the configured `DeepAgent ACP` agent from `.vscode/settings.json`

3. Ask DeepAgent to create an artifact in one of:

- `.acp/tasks/`
- `.acp/messages/`
- `.acp/artifacts/`

4. In Copilot Chat, invoke `consume-deepagent-artifact`.

Expected outcome:
- Copilot reads the latest relevant DeepAgent artifact.
- Copilot verifies the artifact against the live workspace before acting.

5. In Copilot Chat, invoke `delegate-to-deepagent` or `request-deepagent-context`.

Expected outcome:
- Copilot writes a mailbox artifact addressed to `deepagent`.
- The watcher detects the new artifact and prints a notification in the shell.

6. Ask DeepAgent to consume the mailbox request and publish a response artifact.

Expected outcome:
- A full round-trip occurs through the workspace mailbox.

## Success criteria

- The `DeepAgent ACP` launcher constructs successfully in the configured Conda environment.
- The ACP smoke test succeeds over stdio outside VS Code.
- DeepAgent can publish arbitrary tasks or results, not just context.
- Copilot can write DeepAgent-addressed requests using prompt-guided file output.
- The watcher reliably surfaces inbound requests from Copilot.
- Both agents can hand work off without requiring a custom VS Code extension.
