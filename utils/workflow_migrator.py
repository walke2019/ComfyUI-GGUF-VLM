"""Workflow migration helpers for v1 -> v2 node IDs."""

import copy
import json
from pathlib import Path

from .node_replacements import get_node_replacements


def migrate_workflow_dict(workflow: dict) -> dict:
    replacements = get_node_replacements()
    migrated = copy.deepcopy(workflow)
    changed = []
    for node in migrated.get("nodes", []):
        old_type = node.get("type")
        if old_type in replacements:
            node["type"] = replacements[old_type]
            changed.append({"id": node.get("id"), "from": old_type, "to": node["type"]})
    extra = migrated.setdefault("extra", {})
    extra["v2_migration"] = {
        "replacement_count": len(changed),
        "replacements": changed,
    }
    return migrated


def migrate_workflow_file(src, dst=None):
    src_path = Path(src)
    dst_path = Path(dst) if dst else src_path.with_suffix(".v2.json")
    data = json.loads(src_path.read_text(encoding="utf-8"))
    migrated = migrate_workflow_dict(data)
    dst_path.write_text(json.dumps(migrated, ensure_ascii=False, indent=2), encoding="utf-8")
    return dst_path

