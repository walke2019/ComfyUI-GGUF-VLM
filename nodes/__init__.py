"""
ComfyUI node definitions
"""

from .vision_node import VisionLanguageNode, VisionModelLoader
from .memory_manager_node import MemoryManagerNode

# 旧的文本节点已废弃，使用新的 text_generation_nodes
# from .text_node import TextGenerationNode, TextModelLoader

# 导出节点映射（用于向后兼容）
NODE_CLASS_MAPPINGS = {
    "VisionLanguageNode": VisionLanguageNode,
    "VisionModelLoader": VisionModelLoader,
    "MemoryManagerNode": MemoryManagerNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VisionLanguageNode": "🖼️ Vision Language Model (GGUF)",
    "VisionModelLoader": "🖼️ Vision Model Loader (GGUF)",
    "MemoryManagerNode": "🧹 Memory Manager (GGUF)",
}

__all__ = ['VisionLanguageNode', 'VisionModelLoader', 'MemoryManagerNode', 'NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
