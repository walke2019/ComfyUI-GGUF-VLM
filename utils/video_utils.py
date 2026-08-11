"""Video frame utilities for ComfyUI IMAGE batch tensors."""

from typing import List


def select_frame_indices(frame_count: int, max_frames: int, strategy: str = "uniform") -> List[int]:
    """Select representative frame indices.

    Strategies:
    - uniform: spread indices from first to last frame
    - head: first N frames
    - tail: last N frames
    """
    if frame_count <= 0 or max_frames <= 0:
        return []
    if frame_count <= max_frames:
        return list(range(frame_count))

    strategy = (strategy or "uniform").lower()
    if strategy == "head":
        return list(range(max_frames))
    if strategy == "tail":
        return list(range(frame_count - max_frames, frame_count))

    if max_frames == 1:
        return [0]

    step = (frame_count - 1) / (max_frames - 1)
    return [round(i * step) for i in range(max_frames)]

