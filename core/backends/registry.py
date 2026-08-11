"""Backend Adapter 2.0 descriptors."""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class BackendDescriptor:
    key: str
    display_name: str
    protocol: str
    default_port: int
    supports_text: bool
    supports_vision: bool
    supports_video: bool
    supports_streaming: bool


_BACKENDS = [
    BackendDescriptor("openai", "OpenAI Compatible", "openai_compatible", 1234, True, True, False, True),
    BackendDescriptor("lmstudio", "LM Studio", "openai_compatible", 1234, True, True, False, True),
    BackendDescriptor("ollama", "Ollama", "openai_compatible/native", 11434, True, True, False, True),
    BackendDescriptor("llamacpp_server", "llama.cpp server", "openai_compatible/libmtmd", 8080, True, True, True, True),
    BackendDescriptor("nexa", "Nexa SDK", "openai_compatible", 8080, True, True, False, False),
    BackendDescriptor("transformers", "Transformers", "local_python", 0, True, True, True, False),
    BackendDescriptor("local_gguf", "Local GGUF", "llama_cpp_python", 0, True, True, False, False),
]


_ALIASES = {
    "openai compatible": "openai",
    "openai-compatible": "openai",
    "openai": "openai",
    "lm studio": "lmstudio",
    "lmstudio": "lmstudio",
    "ollama": "ollama",
    "llama.cpp server": "llamacpp_server",
    "llamacpp server": "llamacpp_server",
    "llamacpp_server": "llamacpp_server",
    "nexa sdk": "nexa",
    "nexa": "nexa",
    "transformers": "transformers",
    "local gguf": "local_gguf",
    "local_gguf": "local_gguf",
}


def get_backend_descriptors() -> List[BackendDescriptor]:
    return list(_BACKENDS)


def normalize_backend_type(name: str) -> str:
    normalized = (name or "").strip().lower()
    return _ALIASES.get(normalized, normalized.replace(" ", "_").replace("-", "_"))

