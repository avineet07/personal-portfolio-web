"""
llm_client.py — Multi-provider LLM interface with intelligent offline fallback.

Connects to LLM APIs (Gemini, OpenAI, Anthropic) if USE_LLM=true and credentials
are present, or provides a high-fidelity offline fallback engine when disabled.
"""

import json
from typing import Dict, Any, Optional
from .config import (
    USE_LLM,
    LLM_PROVIDER,
    LLM_MODEL,
    GEMINI_API_KEY,
    OPENAI_API_KEY,
    ANTHROPIC_API_KEY,
)


class LLMClient:
    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        enabled: Optional[bool] = None
    ):
        self.enabled = enabled if enabled is not None else USE_LLM
        self.provider = (provider or LLM_PROVIDER or "auto").lower()
        self.api_key = api_key
        self.model = model or LLM_MODEL
        self._init_provider()

    def _init_provider(self):
        """Detect and set up the active provider."""
        if not self.enabled or self.provider == "offline":
            self.active_provider = "offline"
            return

        gemini_key = self.api_key or GEMINI_API_KEY
        openai_key = self.api_key or OPENAI_API_KEY
        anthropic_key = self.api_key or ANTHROPIC_API_KEY

        if (self.provider in ("gemini", "auto")) and gemini_key:
            self.active_provider = "gemini"
            self.api_key = gemini_key
            self.model = self.model or "gemini-1.5-flash"
        elif (self.provider in ("openai", "auto")) and openai_key:
            self.active_provider = "openai"
            self.api_key = openai_key
            self.model = self.model or "gpt-4o-mini"
        elif (self.provider in ("anthropic", "auto")) and anthropic_key:
            self.active_provider = "anthropic"
            self.api_key = anthropic_key
            self.model = self.model or "claude-3-5-haiku-20241022"
        else:
            self.active_provider = "offline"

    def generate_json(self, prompt: str, system_instruction: str = "") -> Optional[Dict[str, Any]]:
        """Calls the configured LLM to generate structured JSON. Returns None if offline/failed."""
        if self.active_provider == "offline":
            return None

        try:
            if self.active_provider == "gemini":
                return self._call_gemini(prompt, system_instruction)
            elif self.active_provider == "openai":
                return self._call_openai(prompt, system_instruction)
            elif self.active_provider == "anthropic":
                return self._call_anthropic(prompt, system_instruction)
        except Exception as e:
            print(f"⚠️ LLM generation failed ({self.active_provider}): {e}. Using fallback values.")
            return None

        return None

    def _clean_json_response(self, text: str) -> Dict[str, Any]:
        """Strip markdown fences and parse JSON safely."""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        return json.loads(text)

    def _call_gemini(self, prompt: str, system_instruction: str) -> Dict[str, Any]:
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": f"{system_instruction}\n\n{prompt}"}]}],
            "generationConfig": {"response_mime_type": "application/json"}
        }
        res = requests.post(url, json=payload, timeout=30)
        res.raise_for_status()
        data = res.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        return self._clean_json_response(raw_text)

    def _call_openai(self, prompt: str, system_instruction: str) -> Dict[str, Any]:
        import requests
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": f"{system_instruction}\nRespond in valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}
        }
        res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
        res.raise_for_status()
        data = res.json()
        raw_text = data["choices"][0]["message"]["content"]
        return self._clean_json_response(raw_text)

    def _call_anthropic(self, prompt: str, system_instruction: str) -> Dict[str, Any]:
        import requests
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "system": f"{system_instruction}\nRespond strictly with a JSON object. No conversational filler.",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        res = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=30)
        res.raise_for_status()
        data = res.json()
        raw_text = data["content"][0]["text"]
        return self._clean_json_response(raw_text)
