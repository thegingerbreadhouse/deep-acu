# ACP Mailbox

The `.acp/` tree has one communication model:

- `.acp/incoming/`: markdown requests from Copilot to the ACP DeepAgent
- `.acp/outgoing/`: markdown responses from the ACP DeepAgent for Copilot
- `.acp/state/`: poller/runtime state

No agent-to-agent communication should happen outside `incoming` and `outgoing`.

## Incoming format

Each incoming file is markdown. Minimal metadata is fine. The body is the source of truth.

Suggested shape:

```text
from: copilot
to: deepagent
---

What are the contents of the .gitignore?
```

## Outgoing format

Each outgoing file is markdown written in response to one incoming file.

Suggested shape:

```text
from: deepagent
to: copilot
request_file: 20260329-...md
status: done
---

# Response

...
```

## Polling behavior

- The poller watches `.acp/incoming/` for new or changed markdown files.
- When a change is detected, it prompts the ACP agent with that request.
- The poller writes the agent's answer to `.acp/outgoing/`.
- If the ACP agent fails, the poller still writes an outgoing file with `status: error`.
- Each turn also writes a JSON observability record under `.acp/state/observability/`.
