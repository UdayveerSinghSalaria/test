"""Configurable LLM client — provider-agnostic, no hardcoded vendor.

Supports:
  * any OpenAI-compatible endpoint (OpenRouter, OpenAI, Gemini, Groq, Ollama...)
    via LLM_PROVIDER=openai-compatible + LLM_BASE_URL
  * Anthropic Messages API via LLM_PROVIDER=anthropic

Only server-side env vars hold the key. Every call is timeout-bounded and
raises LLMError with a user-safe message (never leaking the key).
"""

from __future__ import annotations

import json
import logging

import httpx

from ..config import get_settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    pass


async def chat(messages: list[dict], *, temperature: float = 0.2, max_tokens: int = 2048) -> str:
    """Return the model's text content for a chat message list."""
    settings = get_settings()
    if not settings.llm_configured:
        raise LLMError(
            "LLM is not configured. Set LLM_PROVIDER, LLM_BASE_URL, LLM_MODEL "
            "and LLM_API_KEY in backend/.env."
        )

    provider = settings.llm_provider.lower().strip()
    try:
        if provider == "anthropic":
            return await _chat_anthropic(messages, temperature, max_tokens)
        return await _chat_openai_compatible(messages, temperature, max_tokens)
    except httpx.HTTPError:
        logger.error("LLM endpoint unreachable (provider=%s)", provider)
        raise LLMError("The AI provider could not be reached.") from None
    except json.JSONDecodeError:
        raise LLMError("The AI provider returned an unreadable response.") from None


async def chat_json(messages: list[dict], *, temperature: float = 0.2) -> str:
    """chat() with JSON-only enforcement (OpenAI-compatible structured path)."""
    settings = get_settings()
    provider = settings.llm_provider.lower().strip()
    if provider != "anthropic":
        messages = [*messages, {"role": "system", "content": "Respond with valid JSON only."}]
    return await chat(messages, temperature=temperature)


async def _chat_openai_compatible(messages: list[dict], temperature: float, max_tokens: int) -> str:
    s = get_settings()
    base = s.llm_base_url.rstrip("/")
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {s.llm_api_key}"},
            json={
                "model": s.llm_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
    if resp.status_code == 401:
        raise LLMError("The AI provider rejected the API key (check LLM_API_KEY).")
    if resp.status_code >= 400:
        logger.warning("LLM error %s from openai-compatible endpoint", resp.status_code)
        raise LLMError(f"The AI provider returned an error (HTTP {resp.status_code}).")
    data = resp.json()
    return data["choices"][0]["message"]["content"] or ""


async def _chat_anthropic(messages: list[dict], temperature: float, max_tokens: int) -> str:
    s = get_settings()
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    conv = [m for m in messages if m["role"] != "system"]
    base = (s.llm_base_url or "https://api.anthropic.com/v1").rstrip("/")
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{base}/messages",
            headers={
                "x-api-key": s.llm_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": s.llm_model,
                "system": system,
                "messages": conv,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
    if resp.status_code == 401:
        raise LLMError("The AI provider rejected the API key (check LLM_API_KEY).")
    if resp.status_code >= 400:
        logger.warning("LLM error %s from anthropic endpoint", resp.status_code)
        raise LLMError(f"The AI provider returned an error (HTTP {resp.status_code}).")
    data = resp.json()
    blocks = data.get("content", [])
    return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
