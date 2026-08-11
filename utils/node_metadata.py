"""V3-compatible node metadata helpers.

This is additive metadata for v2 planning; existing v1 ComfyUI node classes keep
their current registration paths.
"""

from dataclasses import asdict, dataclass
from typing import Dict


@dataclass(frozen=True)
class NodeMetadata:
    schema_version: int
    id: str
    display_name: str
    category: str
    inputs: Dict[str, str]
    outputs: Dict[str, str]
    description: str


def build_v3_node_metadata(
    node_id: str,
    display_name: str,
    category: str,
    inputs,
    outputs,
    description: str,
):
    """Build a stable metadata dictionary shaped for future V3 migration."""
    return asdict(
        NodeMetadata(
            schema_version=3,
            id=node_id,
            display_name=display_name,
            category=category,
            inputs=dict(inputs),
            outputs=dict(outputs),
            description=description,
        )
    )

