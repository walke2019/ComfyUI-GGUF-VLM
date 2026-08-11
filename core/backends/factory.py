"""Backend Adapter 2.0 factory and concrete backend wrappers."""

from typing import List, Optional

from .registry import get_backend_descriptors, normalize_backend_type
from .vlm_backend import OpenAICompatibleVLMBackend


class BaseBackendAdapter:
    """Uniform backend interface for v2 nodes."""

    def __init__(self, key: str, engine=None):
        self.key = key
        self.engine = engine
        descriptor = next((item for item in get_backend_descriptors() if item.key == key), None)
        self.descriptor = descriptor
        self.supports_text = bool(descriptor.supports_text) if descriptor else True
        self.supports_vision = bool(descriptor.supports_vision) if descriptor else True
        self.supports_video = bool(descriptor.supports_video) if descriptor else False
        self.supports_streaming = bool(descriptor.supports_streaming) if descriptor else False

    def health_check(self) -> bool:
        if self.engine and hasattr(self.engine, "is_service_available"):
            return bool(self.engine.is_service_available())
        return False

    def list_models(self, force_refresh: bool = False) -> List[str]:
        if self.engine and hasattr(self.engine, "get_available_models"):
            return list(self.engine.get_available_models(force_refresh=force_refresh))
        return []

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
        backend = OpenAICompatibleVLMBackend(self.engine)
        return backend.generate(
            model=model,
            prompt=prompt,
            image_urls=image_urls or [],
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
        )

    def stream_generate(
        self,
        model: str,
        prompt: str,
        image_urls: Optional[List[str]] = None,
        system_prompt: str = "",
        max_tokens: int = 1024,
        temperature: float = 0.2,
        timeout: int = 300,
    ):
        from .vlm_backend import build_openai_vision_messages
        try:
            from ...utils.streaming import collect_openai_stream_chunks
        except ImportError:
            from utils.streaming import collect_openai_stream_chunks

        if not self.engine or not hasattr(self.engine, "chat_completion"):
            return
        response_iter = self.engine.chat_completion(
            model=model,
            messages=build_openai_vision_messages(prompt, image_urls or [], system_prompt),
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
            stream=True,
        )
        yield from collect_openai_stream_chunks(response_iter)


class LMStudioBackend(BaseBackendAdapter):
    def __init__(self, engine=None):
        super().__init__("lmstudio", engine)


class OllamaBackend(BaseBackendAdapter):
    def __init__(self, engine=None):
        super().__init__("ollama", engine)


class LlamaCppServerBackend(BaseBackendAdapter):
    def __init__(self, engine=None):
        super().__init__("llamacpp_server", engine)


class NexaBackend(BaseBackendAdapter):
    def __init__(self, engine=None):
        super().__init__("nexa", engine)


class OpenAIBackend(BaseBackendAdapter):
    def __init__(self, engine=None):
        super().__init__("openai", engine)


class TransformersBackend(BaseBackendAdapter):
    def __init__(self, engine=None):
        super().__init__("transformers", engine)


class LocalGGUFBackend(BaseBackendAdapter):
    def __init__(self, engine=None):
        super().__init__("local_gguf", engine)


_BACKEND_CLASSES = {
    "lmstudio": LMStudioBackend,
    "ollama": OllamaBackend,
    "llamacpp_server": LlamaCppServerBackend,
    "nexa": NexaBackend,
    "openai": OpenAIBackend,
    "transformers": TransformersBackend,
    "local_gguf": LocalGGUFBackend,
}


def create_backend(name: str, engine=None) -> BaseBackendAdapter:
    key = normalize_backend_type(name)
    cls = _BACKEND_CLASSES.get(key, OpenAIBackend)
    return cls(engine=engine)
