# DeepAgent Interop Instructions

When working in this repository, you are not the only agent. A DeepAgent may also be active through ACP in VS Code.

## Shared mailbox

Use the `.acp/` mailbox for communication:

- `.acp/tasks/` for task delegation
- `.acp/messages/` for short notifications or clarification
- `.acp/artifacts/` for context bundles and completion reports

## Rules

- Do not invent a direct ACP channel to DeepAgent.
- If you need DeepAgent to do work, write a mailbox artifact addressed to `deepagent`.
- If DeepAgent has already published an artifact, read it and verify against the current workspace before continuing.
- Do not silently overwrite mailbox files created by another agent.
- Prefer new timestamped files over mutating prior ones unless a prompt explicitly asks you to update `current.md`.

## Preferred behavior

- Use markdown mailbox files with the metadata schema documented in `.acp/README.md`.
- When delegating, be explicit about the goal, relevant files, constraints, and desired output.
- When consuming DeepAgent output, treat it as guidance, not unquestioned truth; always check the live files.
