from __future__ import annotations

from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage
from langchain_core.outputs import LLMResult

from .observability import append_event_from_env


def _message_to_event_payload(message: AIMessage) -> dict[str, Any]:
    content = message.content
    thought_blocks: list[dict[str, Any]] = []
    text_blocks: list[dict[str, Any]] = []

    if isinstance(content, list):
        for block in content:
            if not isinstance(block, dict):
                continue
            block_type = block.get("type")
            if block_type == "thinking":
                thought_blocks.append(block)
            elif block_type == "text":
                text_blocks.append(block)

    return {
        "message_id": message.id,
        "usage_metadata": message.usage_metadata,
        "response_metadata": message.response_metadata,
        "tool_calls": message.tool_calls,
        "invalid_tool_calls": message.invalid_tool_calls,
        "additional_kwargs": message.additional_kwargs,
        "content": content,
        "text": getattr(message, "text", None),
        "thought_blocks": thought_blocks,
        "text_blocks": text_blocks,
    }


class LangChainObservabilityHandler(BaseCallbackHandler):
    raise_error = False

    def _run_id(self, run_id: UUID | str | None) -> str | None:
        if run_id is None:
            return None
        return str(run_id)

    def on_chat_model_start(self, serialized: dict[str, Any], messages: list[list[Any]], *, run_id: UUID, **kwargs: Any) -> Any:
        append_event_from_env(
            {
                "event": "chat_model_start",
                "run_id": self._run_id(run_id),
                "serialized": serialized,
                "message_batches": [[getattr(message, "type", None) for message in batch] for batch in messages],
            }
        )

    def on_llm_new_token(self, token: str, *, run_id: UUID, **kwargs: Any) -> Any:
        append_event_from_env(
            {
                "event": "llm_new_token",
                "run_id": self._run_id(run_id),
                "token": token,
                "chars": len(token),
            }
        )

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, **kwargs: Any) -> Any:
        messages: list[dict[str, Any]] = []
        for generation_batch in response.generations:
            for generation in generation_batch:
                message = getattr(generation, "message", None)
                if isinstance(message, AIMessage):
                    messages.append(_message_to_event_payload(message))
        append_event_from_env(
            {
                "event": "llm_end",
                "run_id": self._run_id(run_id),
                "llm_output": response.llm_output,
                "messages": messages,
            }
        )

    def on_llm_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> Any:
        append_event_from_env(
            {
                "event": "llm_error",
                "run_id": self._run_id(run_id),
                "error_type": type(error).__name__,
                "error_message": str(error),
            }
        )

    def on_tool_start(self, serialized: dict[str, Any], input_str: str, *, run_id: UUID, **kwargs: Any) -> Any:
        append_event_from_env(
            {
                "event": "tool_start",
                "run_id": self._run_id(run_id),
                "tool_name": serialized.get("name"),
                "serialized": serialized,
                "input": input_str,
            }
        )

    def on_tool_end(self, output: Any, *, run_id: UUID, **kwargs: Any) -> Any:
        append_event_from_env(
            {
                "event": "tool_end",
                "run_id": self._run_id(run_id),
                "output_preview": str(output)[:1000],
            }
        )

    def on_tool_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> Any:
        append_event_from_env(
            {
                "event": "tool_error",
                "run_id": self._run_id(run_id),
                "error_type": type(error).__name__,
                "error_message": str(error),
            }
        )

    def on_agent_action(self, action: Any, *, run_id: UUID, **kwargs: Any) -> Any:
        append_event_from_env(
            {
                "event": "agent_action",
                "run_id": self._run_id(run_id),
                "tool": getattr(action, "tool", None),
                "tool_input": getattr(action, "tool_input", None),
                "log": getattr(action, "log", None),
            }
        )

    def on_agent_finish(self, finish: Any, *, run_id: UUID, **kwargs: Any) -> Any:
        append_event_from_env(
            {
                "event": "agent_finish",
                "run_id": self._run_id(run_id),
                "return_values": getattr(finish, "return_values", None),
                "log": getattr(finish, "log", None),
            }
        )
