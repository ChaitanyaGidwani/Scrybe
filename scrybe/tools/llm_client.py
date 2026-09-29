"""Scrybe LLM Client Abstraction.

Provides a unified interface for calling different LLM providers
(OpenAI, Anthropic, Google) with structured JSON output mode,
retry logic, and token usage tracking.
"""

import json
import logging
from typing import Any, Dict, Optional

from scrybe.logging_config import get_agent_logger

logger = get_agent_logger("llm_client")


class LLMClient:
    """Unified LLM client supporting OpenAI, Anthropic, and Google APIs.

    Automatically detects the provider from the model name and routes
    the request accordingly. Falls back gracefully with clear errors.
    """

    def __init__(
        self,
        openai_api_key: str = "",
        anthropic_api_key: str = "",
        google_api_key: str = "",
    ):
        self.openai_api_key = openai_api_key
        self.anthropic_api_key = anthropic_api_key
        self.google_api_key = google_api_key
        self._clients: Dict[str, Any] = {}

    def _get_openai_client(self):
        if "openai" not in self._clients:
            try:
                import openai
                self._clients["openai"] = openai.OpenAI(api_key=self.openai_api_key)
            except ImportError:
                raise RuntimeError("openai package not installed. Run: pip install openai")
        return self._clients["openai"]

    def _get_anthropic_client(self):
        if "anthropic" not in self._clients:
            try:
                import anthropic
                self._clients["anthropic"] = anthropic.Anthropic(api_key=self.anthropic_api_key)
            except ImportError:
                raise RuntimeError("anthropic package not installed. Run: pip install anthropic")
        return self._clients["anthropic"]

    def _detect_provider(self, model: str) -> str:
        """Detect LLM provider from model name."""
        model_lower = model.lower()
        if "claude" in model_lower:
            return "anthropic"
        elif "gemini" in model_lower:
            return "google"
        else:
            return "openai"

    def generate(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        json_mode: bool = True,
    ) -> str:
        """Generate a completion from the appropriate LLM provider.

        Args:
            prompt: The user prompt / content.
            model: Model name (e.g., 'gpt-4o-mini', 'claude-3-5-haiku-20241022').
            system_prompt: Optional system-level instructions.
            temperature: Sampling temperature (0.0 for deterministic).
            max_tokens: Maximum output tokens.
            json_mode: Whether to request JSON output format.

        Returns:
            Raw text response from the LLM.
        """
        provider = self._detect_provider(model)

        logger.info(
            f"LLM call: provider={provider}, model={model}",
            extra={"agent": "llm_client", "step": "generate"},
        )

        if provider == "openai":
            return self._call_openai(prompt, model, system_prompt, temperature, max_tokens, json_mode)
        elif provider == "anthropic":
            return self._call_anthropic(prompt, model, system_prompt, temperature, max_tokens)
        elif provider == "google":
            return self._call_google(prompt, model, temperature, max_tokens)
        else:
            raise ValueError(f"Unknown provider for model: {model}")

    def _call_openai(
        self, prompt: str, model: str, system_prompt: Optional[str],
        temperature: float, max_tokens: int, json_mode: bool,
    ) -> str:
        client = self._get_openai_client()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    def _call_anthropic(
        self, prompt: str, model: str, system_prompt: Optional[str],
        temperature: float, max_tokens: int,
    ) -> str:
        client = self._get_anthropic_client()
        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = client.messages.create(**kwargs)
        return response.content[0].text if response.content else ""

    def _call_google(
        self, prompt: str, model: str, temperature: float, max_tokens: int,
    ) -> str:
        try:
            import google.generativeai as genai
        except ImportError:
            raise RuntimeError("google-generativeai not installed. Run: pip install google-generativeai")

        genai.configure(api_key=self.google_api_key)
        genai_model = genai.GenerativeModel(model)

        config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        response = genai_model.generate_content(prompt, generation_config=config)
        return response.text or ""
