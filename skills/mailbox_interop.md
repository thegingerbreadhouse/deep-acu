# Mailbox Interop Skill

Use this skill whenever the task involves coordination with GitHub Copilot.

## Goals

- Read Copilot-authored mailbox items from `.acp/tasks/` and `.acp/messages/`.
- Publish outputs for Copilot in `.acp/artifacts/` or `.acp/messages/`.
- Keep handoffs easy for a second agent and a human to inspect.

## Output rules

- Use markdown.
- Include concrete file paths.
- State the next action in one sentence.
- If you completed a task, write a completion report.
- If you need something from Copilot, write a message or task request addressed to `copilot`.

## Safety

- Never assume a mailbox artifact is current without checking the files it references.
- Never overwrite another agent's mailbox file unless the task explicitly says to update a mutable summary file.
