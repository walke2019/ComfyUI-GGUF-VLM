"""v2 node aliases and migration targets.

These classes keep the current stable v1 execution behavior while exposing
new v2 node IDs for workflow migration and future V3-native replacement.
"""

try:
    from .business_nodes import DynamicMultiImageCollector, RemoteVLMTaskRunner
    from .remote_vision_node import RemoteVisionAnalysis, RemoteVisionModelConfig
    from .text_node import TextGenerationNode, TextModelLoader
    from .vision_node import VisionLanguageNode, VisionModelLoader
except Exception:
    class _UnavailableNode:
        @classmethod
        def INPUT_TYPES(cls):
            return {"required": {}}

        RETURN_TYPES = ("STRING",)
        FUNCTION = "unavailable"
        CATEGORY = "🤖 GGUF-VLM/v2"

        def unavailable(self):
            return ("V2 node requires ComfyUI runtime dependencies.",)

    DynamicMultiImageCollector = _UnavailableNode
    RemoteVLMTaskRunner = _UnavailableNode
    RemoteVisionAnalysis = _UnavailableNode
    RemoteVisionModelConfig = _UnavailableNode
    TextGenerationNode = _UnavailableNode
    TextModelLoader = _UnavailableNode
    VisionLanguageNode = _UnavailableNode
    VisionModelLoader = _UnavailableNode


class V2RemoteVisionModelConfig(RemoteVisionModelConfig):
    CATEGORY = "🤖 GGUF-VLM/v2/Remote"


class V2RemoteVisionAnalysis(RemoteVisionAnalysis):
    CATEGORY = "🤖 GGUF-VLM/v2/Remote"


class V2LocalVisionModelLoader(VisionModelLoader):
    CATEGORY = "🤖 GGUF-VLM/v2/Local"


class V2LocalVisionAnalysis(VisionLanguageNode):
    CATEGORY = "🤖 GGUF-VLM/v2/Local"


class V2LocalTextModelLoader(TextModelLoader):
    CATEGORY = "🤖 GGUF-VLM/v2/Text"


class V2TextGeneration(TextGenerationNode):
    CATEGORY = "🤖 GGUF-VLM/v2/Text"


class V2DynamicMultiImageAnalysis(DynamicMultiImageCollector):
    CATEGORY = "🤖 GGUF-VLM/v2/Business"


class V2RemoteVLMTaskRunner(RemoteVLMTaskRunner):
    CATEGORY = "🤖 GGUF-VLM/v2/Business"


NODE_CLASS_MAPPINGS = {
    "V2RemoteVisionModelConfig": V2RemoteVisionModelConfig,
    "V2RemoteVisionAnalysis": V2RemoteVisionAnalysis,
    "V2LocalVisionModelLoader": V2LocalVisionModelLoader,
    "V2LocalVisionAnalysis": V2LocalVisionAnalysis,
    "V2LocalTextModelLoader": V2LocalTextModelLoader,
    "V2TextGeneration": V2TextGeneration,
    "V2DynamicMultiImageAnalysis": V2DynamicMultiImageAnalysis,
    "V2RemoteVLMTaskRunner": V2RemoteVLMTaskRunner,
}


NODE_DISPLAY_NAME_MAPPINGS = {
    "V2RemoteVisionModelConfig": "🌐 V2 Remote Vision Model Config",
    "V2RemoteVisionAnalysis": "🔍 V2 Remote Vision Analysis",
    "V2LocalVisionModelLoader": "🖼️ V2 Local Vision Model Loader",
    "V2LocalVisionAnalysis": "🖼️ V2 Local Vision Analysis",
    "V2LocalTextModelLoader": "📋 V2 Local Text Model Loader",
    "V2TextGeneration": "🤖 V2 Text Generation",
    "V2DynamicMultiImageAnalysis": "🧩 V2 Dynamic Multi-Image Analysis",
    "V2RemoteVLMTaskRunner": "🚀 V2 Remote VLM Task Runner",
}
