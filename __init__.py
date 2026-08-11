"""
ComfyUI-GGUF-VLM (Enhanced)
Support for GGUF quantized Vision Language Models + Transformers Models + Text Generation

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

# 可选模型管理器节点（当前仓库未内置 custom_model_manager.py，静默跳过以避免启动噪音）
MANAGER_MAPPINGS = {}
MANAGER_DISPLAY = {}
manager_path = module_path / "custom_model_manager.py"
if manager_path.exists():
    try:
        from .custom_model_manager import NODE_CLASS_MAPPINGS as MANAGER_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as MANAGER_DISPLAY
        print("✅ Model manager loaded")
    except Exception as e:
        print(f"⚠️  Model manager load failed: {e}")

# 导入 GGUF 模式视觉节点
try:
    from .nodes.vision_node import NODE_CLASS_MAPPINGS as VISION_NODES, NODE_DISPLAY_NAME_MAPPINGS as VISION_DISPLAY
    print("✅ Vision nodes (GGUF) loaded")
except Exception as e:
    print(f"⚠️  Vision nodes (GGUF) load failed: {e}")
    VISION_NODES = {}
    VISION_DISPLAY = {}

# 导入文本生成节点（新架构：Local/Remote/Generation）
# 注意：unified_text_node 中的 RemoteTextModelSelector 与 nexa_text_node 中的 RemoteAPIConfig 冲突
# 只加载本地文本模型加载器，远程 API 使用 nexa_text_node
try:
    from .nodes.unified_text_node import NODE_CLASS_MAPPINGS as TEXT_NODES_ALL, NODE_DISPLAY_NAME_MAPPINGS as TEXT_DISPLAY_ALL
    # 只保留本地文本模型相关节点，移除远程 API 节点
    TEXT_NODES = {k: v for k, v in TEXT_NODES_ALL.items() if k not in ["RemoteTextModelSelector"]}
    TEXT_DISPLAY = {k: v for k, v in TEXT_DISPLAY_ALL.items() if k not in ["RemoteTextModelSelector"]}
    print("✅ Text generation nodes loaded (local only)")
except Exception as e:
    print(f"⚠️  Text generation nodes load failed: {e}")
    import traceback
    traceback.print_exc()
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

# 导入业务工作流节点
try:
    from .nodes.business_nodes import NODE_CLASS_MAPPINGS as BUSINESS_NODES, NODE_DISPLAY_NAME_MAPPINGS as BUSINESS_DISPLAY
    print("✅ Business VLM nodes loaded")
except Exception as e:
    print(f"⚠️  Business VLM nodes load failed: {e}")
    BUSINESS_NODES = {}
    BUSINESS_DISPLAY = {}

# 导入 v2 迁移目标节点
try:
    from .nodes.v2_nodes import NODE_CLASS_MAPPINGS as V2_NODES, NODE_DISPLAY_NAME_MAPPINGS as V2_DISPLAY
    print("✅ V2 migration target nodes loaded")
except Exception as e:
    print(f"⚠️  V2 migration target nodes load failed: {e}")
    V2_NODES = {}
    V2_DISPLAY = {}

# 导入 Nexa SDK 节点（新增）
try:
    from .nodes.nexa_text_node import NODE_CLASS_MAPPINGS as NEXA_NODES, NODE_DISPLAY_NAME_MAPPINGS as NEXA_DISPLAY
    print("✅ Nexa SDK nodes loaded")
except Exception as e:
    print(f"⚠️  Nexa SDK nodes load failed: {e}")
    NEXA_NODES = {}
    NEXA_DISPLAY = {}

# 旧的 unified_text_node 已被 text_generation_nodes 替代，不再加载

# 合并所有节点映射
NODE_CLASS_MAPPINGS = {
    **LEGACY_NODES,          # 旧版节点（向后兼容）
    **MANAGER_MAPPINGS,      # 模型管理器
    **VISION_NODES,          # GGUF 模式视觉节点
    **TEXT_NODES,            # 文本生成节点（新架构：Local/Remote/Generation）
    **TRANSFORMERS_NODES,    # Transformers 模式视觉节点
    **MULTI_IMAGE_NODES,     # 多图像分析节点
    **PROMPT_NODES,          # 系统提示词配置节点
    **BUSINESS_NODES,        # Caption/OCR/Prompt/JSON/Video 业务节点
    **V2_NODES,              # v2 迁移目标节点
    **NEXA_NODES,            # Nexa SDK 节点
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **LEGACY_DISPLAY,
    **MANAGER_DISPLAY,
    **VISION_DISPLAY,
    **TEXT_DISPLAY,
    **TRANSFORMERS_DISPLAY,
    **MULTI_IMAGE_DISPLAY,
    **PROMPT_DISPLAY,
    **BUSINESS_DISPLAY,
    **V2_DISPLAY,
    **NEXA_DISPLAY,
}

# 注册 web 目录（前端扩展）
WEB_DIRECTORY = "./web"

# 注册 API 路由（后端端点）
try:
    from . import api_routes
    print("✅ API routes registered")
except Exception as e:
    print(f"⚠️  API routes registration failed: {e}")

print(f"📦 ComfyUI-GGUF-VLM loaded: {len(NODE_CLASS_MAPPINGS)} nodes available")

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']
