"""Streaming helpers for Server-Sent Events and OpenAI-style chunks."""


def sse_event(text: str) -> str:
    """Format a text delta as a simple SSE data event."""
    return f"data: {text}\n\n"


def collect_openai_stream_chunks(chunks):
    """Yield content deltas from OpenAI-compatible streaming chunks."""
    for chunk in chunks:
        content = (
            chunk.get("choices", [{}])[0]
            .get("delta", {})
            .get("content", "")
        )
        if content:
            yield content

