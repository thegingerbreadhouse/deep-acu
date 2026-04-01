from __future__ import annotations

import importlib
import os
from pathlib import Path
from typing import Any

from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.language_models.chat_models import BaseChatModel

DEFAULT_MODEL_FACTORY = "acp_mailbox.model_loader:build_default_chat_model"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


def _load_factory(factory_path: str):
    module_name, _, attr_name = factory_path.partition(":")
    if not module_name or not attr_name:
        raise ValueError(
            "DEEPAGENT_MODEL_FACTORY must use the format 'module.path:function_name'"
        )
    module = importlib.import_module(module_name)
    factory = getattr(module, attr_name, None)
    if factory is None:
        raise ValueError(f"Model factory '{factory_path}' could not be resolved")
    return factory


def _ensure_base_chat_model(model: Any, factory_path: str) -> BaseChatModel:
    if not isinstance(model, BaseChatModel):
        raise TypeError(
            f"Model factory '{factory_path}' must return an instance of BaseChatModel"
        )
    return model


def load_chat_model(workspace_root: Path, callbacks: list[BaseCallbackHandler]) -> BaseChatModel:
    factory_path = os.environ.get("DEEPAGENT_MODEL_FACTORY", DEFAULT_MODEL_FACTORY)
    factory = _load_factory(factory_path)
    model = factory(workspace_root=workspace_root, callbacks=callbacks)
    return _ensure_base_chat_model(model, factory_path)


def build_default_chat_model(
    *,
    workspace_root: Path,
    callbacks: list[BaseCallbackHandler],
) -> BaseChatModel:
    from langchain_google_genai import ChatGoogleGenerativeAI

    model_name = os.environ.get("DEEPAGENT_MODEL", DEFAULT_GEMINI_MODEL)
    return ChatGoogleGenerativeAI(
        model=model_name,
        max_retries=2,
        temperature=1.0,
        include_thoughts=True,
        callbacks=callbacks,
    )
