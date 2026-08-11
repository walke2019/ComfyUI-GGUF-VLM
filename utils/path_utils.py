"""Cross-platform path helpers."""

from pathlib import Path


def path_to_file_url(path) -> str:
    """Convert a local filesystem path to a llama.cpp-compatible file URL."""
    resolved = Path(path).resolve()
    return resolved.as_uri()
