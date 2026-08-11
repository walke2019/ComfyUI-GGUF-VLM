"""Model Catalog 2.0 helpers."""

from pathlib import Path
from typing import Any, Dict, List

import yaml


def load_model_catalog(path) -> Dict[str, Any]:
    catalog_path = Path(path)
    with catalog_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    data.setdefault("models", [])
    return data


def recommend_models(catalog: Dict[str, Any], task: str, max_vram_gb: int) -> List[Dict[str, Any]]:
    task_key = (task or "").strip().lower()
    matches = []
    for order, model in enumerate(catalog.get("models", [])):
        tasks = [str(item).lower() for item in model.get("tasks", [])]
        min_vram = int(model.get("min_vram_gb", 0))
        if task_key in tasks and min_vram <= max_vram_gb:
            item = dict(model)
            item["_catalog_order"] = order
            matches.append(item)
    result = sorted(matches, key=lambda item: (int(item.get("min_vram_gb", 0)), item.get("_catalog_order", 0)))
    for item in result:
        item.pop("_catalog_order", None)
    return result
