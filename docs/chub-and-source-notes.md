# Chub And Source Notes

## Required `chub` lookups

The following lookups were run in this workspace:

```bash
chub search "deepagents" --json
chub search "deepagents-acp" --json
```

Both returned zero curated matches as of 2026-03-29.

The closest curated documentation available through `chub` was:

```bash
chub get langchain/package --lang py
chub get langgraph/package --lang py
```

These were used to ground the LangChain/LangGraph assumptions for agent and persistence behavior.

## `chub feedback` status

Feedback was attempted for both curated docs after use, but the local `chub` configuration has feedback disabled:

```text
Feedback is disabled. Enable with: feedback: true in ~/.chub/config.yaml
```

## Official-source fallback

Because `deepagents` and `deepagents-acp` were not present in `chub`, package-specific behavior should be validated against official upstream docs:

- `deepagents` on PyPI: <https://pypi.org/project/deepagents/>
- `deepagents-acp` reference docs: <https://reference.langchain.com/javascript/deepagents-acp/ide-integration>
- `deepagents` JS reference: <https://reference.langchain.com/javascript/deepagents/agent>

## Python API verified locally

After installing the packages into the Conda environment, the following runtime API surface was verified empirically:

- `deepagents.create_deep_agent(...)` accepts `skills`, `memory`, `backend`, `checkpointer`, `debug`, and `name`.
- `deepagents_acp.server` exposes `AgentServerACP`, `AgentSessionContext`, `FilesystemBackend`, and `run_acp_agent(...)`.
- `AgentSessionContext` includes `cwd` and `mode`.

That local inspection is what this repo's launcher script is based on.

## Practical implication

- `chub` satisfied the curated-doc lookup requirement.
- `deepagents`-specific implementation details still require official-source verification until a curated `chub` entry exists.
- This repo keeps that constraint explicit instead of pretending the package docs were available via `chub`.
