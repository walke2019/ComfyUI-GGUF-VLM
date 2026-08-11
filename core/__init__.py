"""Core module for GGUF model management."""


def _optional_import(module_name, attr_name):
    try:
        module = __import__(f"{__name__}.{module_name}", fromlist=[attr_name])
        return getattr(module, attr_name)
    except Exception:
        return None


ModelLoader = _optional_import("model_loader", "ModelLoader")
InferenceEngine = _optional_import("inference_engine", "InferenceEngine")
CacheManager = _optional_import("cache_manager", "CacheManager")

__all__ = ['ModelLoader', 'InferenceEngine', 'CacheManager']
