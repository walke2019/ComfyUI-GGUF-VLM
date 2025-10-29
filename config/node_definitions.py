"""
Unified Node Definitions - 统一的节点参数定义
确保所有节点使用一致的参数名称和类型
"""

# ============================================================================
# 通用参数定义
# ============================================================================

# Seed 参数 - 统一定义
SEED_INPUT = {
    "seed": (
        "INT",
        {
            "default": 0,
            "min": 0,
            "max": 0xffffffffffffffff,
            "tooltip": "随机种子，用于可重复的生成结果"
        }
    )
}

# 温度参数 - 统一定义（Qwen3-VL 推荐 0.7）
TEMPERATURE_INPUT = {
    "temperature": (
        "FLOAT",
        {
            "default": 0.7,
            "min": 0.0,
            "max": 2.0,
            "step": 0.05,
            "tooltip": "生成温度，控制输出的随机性（Qwen3-VL 推荐: 0.7）"
        }
    )
}

# Top-p 参数（Qwen3-VL 推荐）
TOP_P_INPUT = {
    "top_p": (
        "FLOAT",
        {
            "default": 0.8,
            "min": 0.0,
            "max": 1.0,
            "step": 0.05,
            "tooltip": "Nucleus sampling 参数（Qwen3-VL 推荐: 0.8）"
        }
    )
}

# Top-k 参数（Qwen3-VL 推荐）
TOP_K_INPUT = {
    "top_k": (
        "INT",
        {
            "default": 20,
            "min": 0,
            "max": 100,
            "step": 1,
            "tooltip": "Top-k sampling 参数（Qwen3-VL 推荐: 20）"
        }
    )
}

# Repetition penalty 参数（Qwen3-VL 推荐）
REPETITION_PENALTY_INPUT = {
    "repetition_penalty": (
        "FLOAT",
        {
            "default": 1.0,
            "min": 1.0,
            "max": 2.0,
            "step": 0.05,
            "tooltip": "重复惩罚（Qwen3-VL 推荐: 1.0）"
        }
    )
}

# 最大 token 数 - 统一定义
MAX_TOKENS_INPUT = {
    "max_tokens": (
        "INT",
        {
            "default": 512,
            "min": 1,
            "max": 32768,
            "step": 1,
            "tooltip": "最大生成 token 数"
        }
    )
}

# 提示词输入 - 统一定义
PROMPT_INPUT = {
    "prompt": (
        "STRING",
        {
            "default": "Describe this image in detail.",
            "multiline": True,
            "tooltip": "用户提示词"
        }
    )
}

# 系统提示词输入 - 统一定义（可选）
SYSTEM_PROMPT_INPUT = {
    "system_prompt": (
        "STRING",
        {
            "default": "",
            "multiline": True,
            "tooltip": "系统提示词（可选）"
        }
    )
}

# ============================================================================
# 统一的输出类型定义
# ============================================================================

# 文本输出 - 统一名称
TEXT_OUTPUT = {
    "types": ("STRING",),
    "names": ("context",)
}

# 描述输出 - 用于图像描述
DESCRIPTION_OUTPUT = {
    "types": ("STRING",),
    "names": ("context",)
}

# 模型配置输出
MODEL_CONFIG_OUTPUT = {
    "types": ("MODEL_CONFIG",),
    "names": ("model_config",)
}

# GGUF 模型输出
GGUF_MODEL_OUTPUT = {
    "types": ("VISION_MODEL",),
    "names": ("vision_model",)
}

# Transformers 模型输出
TRANSFORMERS_MODEL_OUTPUT = {
    "types": ("TRANSFORMERS_MODEL",),
    "names": ("model_config",)
}

# ============================================================================
# GGUF 模式特定参数
# ============================================================================

GGUF_CONTEXT_INPUT = {
    "n_ctx": (
        "INT",
        {
            "default": 8192,
            "min": 512,
            "max": 128000,
            "step": 512,
            "tooltip": "上下文窗口大小"
        }
    )
}

GGUF_DEVICE_INPUT = {
    "device": (
        ["Auto", "GPU", "CPU"],
        {
            "default": "Auto",
            "tooltip": "运行设备"
        }
    )
}

# ============================================================================
# Transformers 模式特定参数
# ============================================================================

TRANSFORMERS_QUANTIZATION_INPUT = {
    "quantization": (
        ["none", "4bit", "8bit"],
        {
            "default": "none",
            "tooltip": "量化类型"
        }
    )
}

TRANSFORMERS_ATTENTION_INPUT = {
    "attention": (
        ["eager", "sdpa", "flash_attention_2"],
        {
            "default": "flash_attention_2",
            "tooltip": "注意力机制实现（Qwen3-VL 推荐: flash_attention_2）"
        }
    )
}

TRANSFORMERS_PIXELS_INPUT = {
    "min_pixels": (
        "INT",
        {
            "default": 256 * 28 * 28,
            "min": 4 * 28 * 28,
            "max": 16384 * 28 * 28,
            "step": 28 * 28,
            "tooltip": "最小像素数"
        }
    ),
    "max_pixels": (
        "INT",
        {
            "default": 1280 * 28 * 28,
            "min": 4 * 28 * 28,
            "max": 16384 * 28 * 28,
            "step": 28 * 28,
            "tooltip": "最大像素数"
        }
    )
}

# ============================================================================
# 通用选项
# ============================================================================

KEEP_MODEL_LOADED_INPUT = {
    "keep_model_loaded": (
        "BOOLEAN",
        {
            "default": False,
            "tooltip": "推理后是否保持模型加载在内存中"
        }
    )
}

# ============================================================================
# 辅助函数
# ============================================================================

def merge_inputs(*input_dicts):
    """
    合并多个输入定义字典
    
    Args:
        *input_dicts: 多个输入定义字典
    
    Returns:
        合并后的字典
    """
    result = {}
    for input_dict in input_dicts:
        result.update(input_dict)
    return result


def get_common_generation_inputs():
    """获取通用的生成参数"""
    return merge_inputs(
        PROMPT_INPUT,
        TEMPERATURE_INPUT,
        MAX_TOKENS_INPUT,
        SEED_INPUT
    )


def get_qwen3_generation_inputs():
    """获取 Qwen3-VL 推荐的生成参数"""
    return merge_inputs(
        PROMPT_INPUT,
        TEMPERATURE_INPUT,
        TOP_P_INPUT,
        TOP_K_INPUT,
        REPETITION_PENALTY_INPUT,
        MAX_TOKENS_INPUT,
        SEED_INPUT
    )


def get_gguf_model_inputs():
    """获取 GGUF 模式的模型参数"""
    return merge_inputs(
        GGUF_CONTEXT_INPUT,
        GGUF_DEVICE_INPUT
    )


def get_transformers_model_inputs():
    """获取 Transformers 模式的模型参数"""
    return merge_inputs(
        TRANSFORMERS_QUANTIZATION_INPUT,
        TRANSFORMERS_ATTENTION_INPUT,
        TRANSFORMERS_PIXELS_INPUT,
        KEEP_MODEL_LOADED_INPUT
    )
