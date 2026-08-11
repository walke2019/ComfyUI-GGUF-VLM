"""Unified VLM backend adapters."""

from typing import Any, Dict, List, Optional


def build_openai_vision_messages(
    prompt: str,
    image_urls: Optional[List[str]] = None,
    system_prompt: str = "",
) -> List[Dict[str, Any]]:
    """Build OpenAI-compatible vision chat messages."""
    messages: List[Dict[str, Any]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    image_urls = image_urls or []
    if image_urls:
        content: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
        content.extend(
            {"type": "image_url", "image_url": {"url": url}}
            for url in image_urls
        )
        messages.append({"role": "user", "content": content})
    else:
        messages.append({"role": "user", "content": prompt})

    return messages


class OpenAICompatibleVLMBackend:
    """Thin adapter around the existing UnifiedAPIEngine."""

    def __init__(self, engine):
        self.engine = engine

    def generate(
        self,
        model: str,
        prompt: str,
        image_urls: Optional[List[str]] = None,
        system_prompt: str = "",
        max_tokens: int = 1024,
        temperature: float = 0.2,
        timeout: int = 300,
    ) -> str:
        messages = build_openai_vision_messages(prompt, image_urls, system_prompt)
        response = self.engine.chat_completion(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
        )
        return response["choices"][0]["message"]["content"].strip()

