"""
ComfyUI-GGUF-VisionLM (Enhanced)
Support for GGUF quantized Vision Language Models + Transformers Models

三模式支持：
1. GGUF 模式：使用 llama-cpp-python，支持量化模型（Q8_0, Q4_K_M等）
2. Transformers 模式：使用 HuggingFace Transformers，支持完整模型
3. Nexa SDK 模式：使用 Nexa SDK 服务，支持远程推理

多图像分析：
- 支持最多 6 张图像同时输入
- 图像对比、相似性分析、变化检测等

模块化架构：
- core/: 核心功能（模型加载、推理引擎、缓存管理）
  - inference/: 推理引擎（GGUF, Transformers, Nexa SDK）
- models/: 模型配置（视觉模型、文本模型）
- utils/: 工具函数（下载器、验证器、注册表、系统提示词）
- nodes/: ComfyUI 节点定义
  - vision_node.py: GGUF 模式视觉节点
  - vision_node_transformers.py: Transformers 模式视觉节点
  - multi_image_node.py: 多图像分析节点
  - system_prompt_node.py: 系统提示词配置节点
  - nexa_text_node.py: Nexa SDK 文本生成节点
- config/: 配置文件
"""

import sys
from pathlib import Path

# 确保模块路径正确
module_path = Path(__file__).parent
if str(module_path) not in sys.path:
    sys.path.insert(0, str(module_path))

# 导入旧版节点（向后兼容）
try:
    from .nodes import NODE_CLASS_MAPPINGS as LEGACY_NODES, NODE_DISPLAY_NAME_MAPPINGS as LEGACY_DISPLAY
    print("✅ Legacy nodes loaded")
except Exception as e:
    print(f"⚠️  Legacy nodes load failed: {e}")
    LEGACY_NODES = {}
    LEGACY_DISPLAY = {}

# 导入模型管理器节点
try:
    from .custom_model_manager import NODE_CLASS_MAPPINGS as MANAGER_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as MANAGER_DISPLAY
    print("✅ Model manager loaded")
except Exception as e:
    print(f"⚠️  Model manager load failed: {e}")
    MANAGER_MAPPINGS = {}
    MANAGER_DISPLAY = {}

# 导入 GGUF 模式视觉节点
try:
    from .nodes.vision_node import NODE_CLASS_MAPPINGS as VISION_NODES, NODE_DISPLAY_NAME_MAPPINGS as VISION_DISPLAY
    print("✅ Vision nodes (GGUF) loaded")
except Exception as e:
    print(f"⚠️  Vision nodes (GGUF) load failed: {e}")
    VISION_NODES = {}
    VISION_DISPLAY = {}

# 导入文本节点
try:
    from .nodes.text_node import NODE_CLASS_MAPPINGS as TEXT_NODES, NODE_DISPLAY_NAME_MAPPINGS as TEXT_DISPLAY
    print("✅ Text nodes loaded")
except Exception as e:
    print(f"⚠️  Text nodes load failed: {e}")
    TEXT_NODES = {}
    TEXT_DISPLAY = {}

# 导入 Transformers 模式视觉节点
try:
    from .nodes.vision_node_transformers import NODE_CLASS_MAPPINGS as TRANSFORMERS_NODES, NODE_DISPLAY_NAME_MAPPINGS as TRANSFORMERS_DISPLAY
    print("✅ Vision nodes (Transformers) loaded")
except Exception as e:
    print(f"⚠️  Vision nodes (Transformers) load failed: {e}")
    TRANSFORMERS_NODES = {}
    TRANSFORMERS_DISPLAY = {}

# 导入多图像分析节点
try:
    from .nodes.multi_image_node import NODE_CLASS_MAPPINGS as MULTI_IMAGE_NODES, NODE_DISPLAY_NAME_MAPPINGS as MULTI_IMAGE_DISPLAY
    print("✅ Multi-image analysis nodes loaded")
except Exception as e:
    print(f"⚠️  Multi-image analysis nodes load failed: {e}")
    MULTI_IMAGE_NODES = {}
    MULTI_IMAGE_DISPLAY = {}

# 导入系统提示词配置节点
try:
    from .nodes.system_prompt_node import NODE_CLASS_MAPPINGS as PROMPT_NODES, NODE_DISPLAY_NAME_MAPPINGS as PROMPT_DISPLAY
    print("✅ System prompt config loaded")
except Exception as e:
    print(f"⚠️  System prompt config load failed: {e}")
    PROMPT_NODES = {}
    PROMPT_DISPLAY = {}

# 导入 Nexa SDK 节点（新增）
try:
    from .nodes.nexa_text_node import NODE_CLASS_MAPPINGS as NEXA_NODES, NODE_DISPLAY_NAME_MAPPINGS as NEXA_DISPLAY
    print("✅ Nexa SDK nodes loaded")
except Exception as e:
    print(f"⚠️  Nexa SDK nodes load failed: {e}")
    NEXA_NODES = {}
    NEXA_DISPLAY = {}

# 导入统一文本节点（新增）
try:
    from .nodes.unified_text_node import NODE_CLASS_MAPPINGS as UNIFIED_NODES, NODE_DISPLAY_NAME_MAPPINGS as UNIFIED_DISPLAY
    print("✅ Unified text nodes loaded")
except Exception as e:
    print(f"⚠️  Unified text nodes load failed: {e}")
    UNIFIED_NODES = {}
    UNIFIED_DISPLAY = {}

# 合并所有节点映射
NODE_CLASS_MAPPINGS = {
    **LEGACY_NODES,          # 旧版节点（向后兼容）
    **MANAGER_MAPPINGS,      # 模型管理器
    **VISION_NODES,          # GGUF 模式视觉节点
    **TEXT_NODES,            # 文本节点
    **TRANSFORMERS_NODES,    # Transformers 模式视觉节点
    **MULTI_IMAGE_NODES,     # 多图像分析节点
    **PROMPT_NODES,          # 系统提示词配置节点
    **NEXA_NODES,            # Nexa SDK 节点（新增）
    **UNIFIED_NODES,         # 统一文本节点（新增）
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **LEGACY_DISPLAY,
    **MANAGER_DISPLAY,
    **VISION_DISPLAY,
    **TEXT_DISPLAY,
    **TRANSFORMERS_DISPLAY,
    **MULTI_IMAGE_DISPLAY,
    **PROMPT_DISPLAY,
    **NEXA_DISPLAY,
    **UNIFIED_DISPLAY,
}

print(f"📦 ComfyUI-GGUF-VisionLM (Enhanced) loaded: {len(NODE_CLASS_MAPPINGS)} nodes available")
print(f"   🔹 GGUF Mode: Optimized quantized models")
print(f"   🔹 Transformers Mode: Full HuggingFace models")
print(f"   🔹 Nexa SDK Mode: Remote inference service")
print(f"   🔹 Multi-Image: Up to 6 images analysis")
print(f"   🔹 System Prompt: Configurable presets")

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
