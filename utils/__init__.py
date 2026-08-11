"""Utility module for GGUF operations.

Keep package imports lightweight: optional heavy dependencies such as
requests/tqdm/huggingface_hub should not break unrelated helper imports.
"""


def _optional_import(module_name, attr_name):
    try:
        module = __import__(f"{__name__}.{module_name}", fromlist=[attr_name])
        return getattr(module, attr_name)
    except Exception:
        return None


FileDownloader = _optional_import("downloader", "FileDownloader")
ModelValidator = _optional_import("validator", "ModelValidator")
RegistryManager = _optional_import("registry", "RegistryManager")
DeviceOptimizer = _optional_import("device_optimizer", "DeviceOptimizer")
MMProjFinder = _optional_import("mmproj_finder", "MMProjFinder")
MMProjValidator = _optional_import("mmproj_validator", "MMProjValidator")
SystemPromptsManager = _optional_import("system_prompts", "SystemPromptsManager")
DownloadManager = _optional_import("download_manager", "DownloadManager")
get_download_manager = _optional_import("download_manager", "get_download_manager")

__all__ = [
    'FileDownloader', 
    'ModelValidator', 
    'RegistryManager',
    'DeviceOptimizer',
    'MMProjFinder',
    'MMProjValidator',
    'SystemPromptsManager',
    'DownloadManager',
    'get_download_manager',
]
