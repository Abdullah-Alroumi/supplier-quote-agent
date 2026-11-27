"""Model factory. Provider-agnostic: set QUOTE_AGENT_MODEL to any LangChain 'provider:model' string."""
from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

DEFAULT_MODEL = "google_genai:gemini-3.5-flash"  # free tier via Google AI Studio


def get_model(model: str | None = None):
    """Examples: 'google_genai:gemini-3.5-flash' (free tier, GOOGLE_API_KEY),
    'anthropic:claude-sonnet-5-5' (ANTHROPIC_API_KEY), 'openai:gpt-4.1' (needs langchain-openai)."""
    return init_chat_model(model or os.getenv("QUOTE_AGENT_MODEL", DEFAULT_MODEL), temperature=0)
