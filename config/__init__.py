"""
Configuration module for unified node definitions and paths
"""

from .node_definitions import (
    # 通用参数
    SEED_INPUT,
    TEMPERATURE_INPUT,
    MAX_TOKENS_INPUT,
    PROMPT_INPUT,
    SYSTEM_PROMPT_INPUT,
    
    # 输出定义
    TEXT_OUTPUT,
    DESCRIPTION_OUTPUT,
    MODEL_CONFIG_OUTPUT,
    GGUF_MODEL_OUTPUT,
    TRANSFORMERS_MODEL_OUTPUT,
    
    # GGUF 特定
    GGUF_CONTEXT_INPUT,
    GGUF_DEVICE_INPUT,
    
    # Transformers 特定
    TRANSFORMERS_QUANTIZATION_INPUT,
    TRANSFORMERS_ATTENTION_INPUT,
    TRANSFORMERS_PIXELS_INPUT,
    
    # 通用选项
    KEEP_MODEL_LOADED_INPUT,
    
    # 辅助函数
    merge_inputs,
    get_common_generation_inputs,
    get_gguf_model_inputs,
    get_transformers_model_inputs,
)

from .paths import (
    PathConfig,
    LLM_MODELS_DIR,
    GGUF_MODELS_DIR,
    CLIP_MODELS_DIR,
)

__all__ = [
    # 参数定义
    'SEED_INPUT',
    'TEMPERATURE_INPUT',
    'MAX_TOKENS_INPUT',
    'PROMPT_INPUT',
    'SYSTEM_PROMPT_INPUT',
    'TEXT_OUTPUT',
    'DESCRIPTION_OUTPUT',
    'MODEL_CONFIG_OUTPUT',
    'GGUF_MODEL_OUTPUT',
    'TRANSFORMERS_MODEL_OUTPUT',
    'GGUF_CONTEXT_INPUT',
    'GGUF_DEVICE_INPUT',
    'TRANSFORMERS_QUANTIZATION_INPUT',
    'TRANSFORMERS_ATTENTION_INPUT',
    'TRANSFORMERS_PIXELS_INPUT',
    'KEEP_MODEL_LOADED_INPUT',
    'merge_inputs',
    'get_common_generation_inputs',
    'get_gguf_model_inputs',
    'get_transformers_model_inputs',
    
    # 路径配置
    'PathConfig',
    'LLM_MODELS_DIR',
    'GGUF_MODELS_DIR',
    'CLIP_MODELS_DIR',
]
