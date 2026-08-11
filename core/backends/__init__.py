"""Backend adapters for VLM inference."""

from .vlm_backend import OpenAICompatibleVLMBackend, build_openai_vision_messages
from .registry import BackendDescriptor, get_backend_descriptors, normalize_backend_type
from .factory import (
    BaseBackendAdapter,
    LMStudioBackend,
    OllamaBackend,
    LlamaCppServerBackend,
    NexaBackend,
    OpenAIBackend,
    TransformersBackend,
    LocalGGUFBackend,
    create_backend,
)

__all__ = [
    "OpenAICompatibleVLMBackend",
    "build_openai_vision_messages",
    "BackendDescriptor",
    "get_backend_descriptors",
    "normalize_backend_type",
    "BaseBackendAdapter",
    "LMStudioBackend",
    "OllamaBackend",
    "LlamaCppServerBackend",
    "NexaBackend",
    "OpenAIBackend",
    "TransformersBackend",
    "LocalGGUFBackend",
    "create_backend",
]
