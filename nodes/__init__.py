"""
ComfyUI node definitions
"""

from .vision_node import VisionLanguageNode, VisionModelLoader
from .memory_manager_node import MemoryManagerNode
from .remote_vision_node import RemoteVisionModelConfig, RemoteVisionAnalysis
from .business_nodes import (
    CaptionPromptBuilder,
    OCRPromptBuilder,
    PromptReverseBuilder,
    JSONPromptBuilder,
    RemoteVLMTaskRunner,
    VideoFrameSampler,
    VLMModelAdvisor,
    JSONResultValidator,
    BatchRemoteVLMTask,
    DynamicMultiImageCollector,
)

# 旧的文本节点已废弃，使用新的 text_generation_nodes
# from .text_node import TextGenerationNode, TextModelLoader

# 导出节点映射（用于向后兼容）
NODE_CLASS_MAPPINGS = {
    "VisionLanguageNode": VisionLanguageNode,
    "VisionModelLoader": VisionModelLoader,
    "MemoryManagerNode": MemoryManagerNode,
    "RemoteVisionModelConfig": RemoteVisionModelConfig,
    "RemoteVisionAnalysis": RemoteVisionAnalysis,
    "CaptionPromptBuilder": CaptionPromptBuilder,
    "OCRPromptBuilder": OCRPromptBuilder,
    "PromptReverseBuilder": PromptReverseBuilder,
    "JSONPromptBuilder": JSONPromptBuilder,
    "RemoteVLMTaskRunner": RemoteVLMTaskRunner,
    "VideoFrameSampler": VideoFrameSampler,
    "VLMModelAdvisor": VLMModelAdvisor,
    "JSONResultValidator": JSONResultValidator,
    "BatchRemoteVLMTask": BatchRemoteVLMTask,
    "DynamicMultiImageCollector": DynamicMultiImageCollector,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VisionLanguageNode": "🖼️ Vision Language Model (GGUF)",
    "VisionModelLoader": "🖼️ Vision Model Loader (GGUF)",
    "MemoryManagerNode": "🧹 Memory Manager (GGUF)",
    "RemoteVisionModelConfig": "🌐 Remote Vision Model Config (LM Studio/Ollama)",
    "RemoteVisionAnalysis": "🖼️ Remote Vision Analysis",
    "CaptionPromptBuilder": "🏷️ Caption Prompt Builder",
    "OCRPromptBuilder": "🔤 OCR Prompt Builder",
    "PromptReverseBuilder": "🎨 Prompt Reverse Builder",
    "JSONPromptBuilder": "🧾 JSON Extraction Prompt Builder",
    "RemoteVLMTaskRunner": "🚀 Remote VLM Business Task",
    "VideoFrameSampler": "🎞️ Video Frame Sampler",
    "VLMModelAdvisor": "🧭 VLM Model Advisor",
    "JSONResultValidator": "✅ JSON Result Validator",
    "BatchRemoteVLMTask": "📦 Batch Remote VLM Task",
    "DynamicMultiImageCollector": "🧩 Dynamic Multi-Image Collector",
}

__all__ = [
    'VisionLanguageNode', 'VisionModelLoader', 'MemoryManagerNode',
    'RemoteVisionModelConfig', 'RemoteVisionAnalysis',
    'CaptionPromptBuilder', 'OCRPromptBuilder', 'PromptReverseBuilder',
    'JSONPromptBuilder', 'RemoteVLMTaskRunner', 'VideoFrameSampler',
    'VLMModelAdvisor', 'JSONResultValidator', 'BatchRemoteVLMTask',
    'DynamicMultiImageCollector',
    'NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS'
]
