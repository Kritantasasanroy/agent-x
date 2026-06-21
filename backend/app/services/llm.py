"""Provider-agnostic LLM client.

One `chat()` call routes to OpenAI / Anthropic / Gemini / Ollama based on settings,
with a deterministic offline fallback so the system runs (degraded) with no API key.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("llm")


class LLMUnavailable(Exception):
    pass


class LLMClient:
    def __init__(self, provider: str | None = None) -> None:
        self.provider = (provider or settings.llm_provider).lower()

    # --------------------------------------------------------------------- #
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10), reraise=True)
    def chat(self, system: str, user: str, *, json_mode: bool = False, max_tokens: int = 1500) -> str:
        try:
            if self.provider == "anthropic" and settings.anthropic_api_key:
                return self._anthropic(system, user, max_tokens)
            if self.provider == "openai" and settings.openai_api_key:
                return self._openai(system, user, json_mode, max_tokens)
            if self.provider == "gemini" and settings.gemini_api_key:
                return self._gemini(system, user, max_tokens)
            if self.provider == "ollama":
                return self._ollama(system, user, max_tokens)
        except Exception as exc:  # noqa: BLE001
            log.warning("llm_call_failed", provider=self.provider, error=str(exc))
        return self._fallback(system, user, json_mode)

    def json(self, system: str, user: str, **kw: Any) -> dict:
        raw = self.chat(system, user, json_mode=True, **kw)
        try:
            start, end = raw.find("{"), raw.rfind("}")
            return json.loads(raw[start : end + 1]) if start >= 0 else {}
        except json.JSONDecodeError:
            return {}

    # --------------------------------------------------------------------- #
    def _anthropic(self, system: str, user: str, max_tokens: int) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        msg = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text

    def _openai(self, system: str, user: str, json_mode: bool, max_tokens: int) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        kwargs: dict[str, Any] = {"max_tokens": max_tokens}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        resp = client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            **kwargs,
        )
        return resp.choices[0].message.content or ""

    def _gemini(self, system: str, user: str, max_tokens: int) -> str:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(settings.gemini_model, system_instruction=system)
        resp = model.generate_content(
            user, generation_config={"max_output_tokens": max_tokens}
        )
        return resp.text

    def _ollama(self, system: str, user: str, max_tokens: int) -> str:
        resp = httpx.post(
            f"{settings.ollama_base_url}/api/chat",
            json={
                "model": settings.ollama_model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "options": {"num_predict": max_tokens},
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]

    # --------------------------------------------------------------------- #
    def _fallback(self, system: str, user: str, json_mode: bool) -> str:
        """No provider available: return a safe, structured stub so the pipeline survives."""
        log.info("llm_fallback_used")
        if json_mode:
            return "{}"
        return (
            "[LLM unavailable — offline fallback]\n"
            "Configure an API key (LLM_PROVIDER + *_API_KEY) for real generation.\n"
            f"Context received: {user[:280]}"
        )


def get_llm() -> LLMClient:
    return LLMClient()
