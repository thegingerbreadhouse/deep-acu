# ACP Mailbox Protocol

The `.acp/` tree is the shared interoperability surface between DeepAgent and Copilot.

## Directories

- `tasks/`: task requests and task state transitions
- `messages/`: lightweight notifications and clarifications
- `artifacts/`: larger outputs, context bundles, and completion reports
- `templates/`: canonical markdown templates
- `state/`: watcher runtime state; ignored by git

## Metadata schema

All mailbox files should begin with this metadata block:

```text
id: <unique-id>
from: <deepagent|copilot|user>
to: <deepagent|copilot|user|all>
kind: <task|message|context|completion|review>
status: <new|in_progress|blocked|done|needs_review>
related_files:
  - path/one
  - path/two
next_action: <one-line instruction>
---
```

Follow the metadata block with markdown body content.

## Conventions

- Use one file per exchange. Avoid silent overwrites.
- Prefer append-only timestamps in filenames when creating new work items.
- Use `current.md` only for intentionally mutable summary views.
- Receiving agents must verify workspace reality before acting on a mailbox artifact.
