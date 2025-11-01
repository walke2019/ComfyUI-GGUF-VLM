"""
Path Configuration - 路径配置
统一管理所有模型和文件路径
"""

import os
import folder_paths


class PathConfig:
    """路径配置管理器"""
    
    # ============================================================================
    # 模型目录配置
    # ============================================================================
    
    # LLM 模型目录（Transformers 模式）
    LLM_MODELS_DIR = "LLM"  # Transformers 完整模型目录
    
    # GGUF 模型目录
    GGUF_MODELS_DIR = "LLM"  # GGUF 单文件模型也放在 LLM 目录
    
    # CLIP 模型目录（用于 mmproj 文件）
    CLIP_MODELS_DIR = "LLM/GGUF"
    
    # VAE 模型目录
    VAE_MODELS_DIR = "LLM/GGUF"
    
    # ============================================================================
    # 辅助方法
    # ============================================================================
    
    @classmethod
    def get_llm_models_path(cls):
        """
        获取 LLM 模型目录的完整路径
        
        Returns:
            LLM 模型目录的绝对路径
        """
        path = os.path.join(folder_paths.models_dir, cls.LLM_MODELS_DIR)
        os.makedirs(path, exist_ok=True)
        return path
    
    @classmethod
    def get_gguf_models_path(cls):
        """
        获取 GGUF 模型目录的完整路径
        
        Returns:
            GGUF 模型目录的绝对路径
        """
        path = os.path.join(folder_paths.models_dir, cls.GGUF_MODELS_DIR)
        os.makedirs(path, exist_ok=True)
        return path
    
    @classmethod
    def get_clip_models_path(cls):
        """
        获取 CLIP 模型目录的完整路径（用于 mmproj 文件）
        
        Returns:
            CLIP 模型目录的绝对路径
        """
        return folder_paths.get_folder_paths("clip")[0]
    
    @classmethod
    def get_model_path(cls, model_type, model_name):
        """
        获取特定模型的完整路径
        
        Args:
            model_type: 模型类型 ("llm", "gguf", "clip")
            model_name: 模型名称或 ID
        
        Returns:
            模型的完整路径
        """
        if model_type == "llm":
            base_path = cls.get_llm_models_path()
        elif model_type == "gguf":
            base_path = cls.get_gguf_models_path()
        elif model_type == "clip":
            base_path = cls.get_clip_models_path()
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        return os.path.join(base_path, os.path.basename(model_name))
    
    @classmethod
    def list_models(cls, model_type):
        """
        列出指定类型的所有模型
        
        Args:
            model_type: 模型类型 ("llm", "gguf", "clip")
        
        Returns:
            模型列表
        """
        if model_type == "llm":
            base_path = cls.get_llm_models_path()
        elif model_type == "gguf":
            base_path = cls.get_gguf_models_path()
        elif model_type == "clip":
            base_path = cls.get_clip_models_path()
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        if not os.path.exists(base_path):
            return []
        
        models = []
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path) or item.endswith(('.gguf', '.safetensors', '.bin')):
                models.append(item)
        
        return sorted(models)


# ============================================================================
# 向后兼容的常量
# ============================================================================

# LLM 模型目录
LLM_MODELS_DIR = PathConfig.LLM_MODELS_DIR

# GGUF 模型目录
GGUF_MODELS_DIR = PathConfig.GGUF_MODELS_DIR

# CLIP 模型目录
CLIP_MODELS_DIR = PathConfig.CLIP_MODELS_DIR
