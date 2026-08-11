"""Node replacement map for v2 workflow migration."""


_NODE_REPLACEMENTS = {
    "VisionLanguageNode": "V2LocalVisionAnalysis",
    "VisionModelLoader": "V2LocalVisionModelLoader",
    "RemoteVisionAnalysis": "V2RemoteVisionAnalysis",
    "RemoteVisionModelConfig": "V2RemoteVisionModelConfig",
    "TextGeneration": "V2TextGeneration",
    "LocalTextModelLoader": "V2LocalTextModelLoader",
    "MultiImageAnalysis": "V2DynamicMultiImageAnalysis",
}


def get_node_replacements():
    return dict(_NODE_REPLACEMENTS)

