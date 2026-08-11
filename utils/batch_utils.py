"""Batch workflow helpers."""


def build_batch_labels(prefix: str, count: int):
    clean_prefix = (prefix or "item").strip().replace(" ", "_")
    return [f"{clean_prefix}_{index:04d}" for index in range(1, max(0, int(count)) + 1)]

