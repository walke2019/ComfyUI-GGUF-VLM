"""
Nexa SDK Text Node - 使用 Nexa SDK 服务的文本生成节点
支持本地模型路径管理、自动下载和与 ComfyUI 的 /models/LLM 目录集成
"""

import re
import os
from typing import Tuple
from comfy.comfy_types import IO

# 尝试导入路径配置
try:
    from ..config.paths import PathConfig
    HAS_PATH_CONFIG = True
except:
    HAS_PATH_CONFIG = False
    print("⚠️  PathConfig not available, using default paths")

from ..core.inference.nexa_engine import get_nexa_engine


# Nexa SDK 预设模型列表
# 格式: author/model-name:quant
# 使用前需要先运行: nexa pull <model-name>
PRESET_MODELS = [
    "Custom (输入自定义模型 ID)",
    "DavidAU/Qwen3-8B-64k-Josiefied-Uncensored-HORROR-Max-GGUF:Q6_K",
    "mradermacher/Huihui-Qwen3-4B-Thinking-2507-abliterated-GGUF:Q8_0",
    "prithivMLmods/Qwen3-4B-2507-abliterated-GGUF:Q8_0",
    "mradermacher/Qwen3-4B-Thinking-2507-Uncensored-Fixed-GGUF:Q8_0",
    "mradermacher/Qwen3-Short-Story-Instruct-Uncensored-262K-ctx-4B-GGUF:Q8_0",
]

# HuggingFace URL 到模型 ID 的映射
HUGGINGFACE_URL_MAPPING = {
    "https://huggingface.co/prithivMLmods/Qwen3-4B-2507-abliterated-GGUF/blob/main/Qwen3-4B-Instruct-2507-abliterated-GGUF/Qwen3-4B-Instruct-2507-abliterated.Q8_0.gguf": "🤖 prithivMLmods/Qwen3-4B-2507-abliterated-GGUF:Q8_0",
    
    "https://huggingface.co/mradermacher/Qwen3-4B-Thinking-2507-Uncensored-Fixed-GGUF/resolve/main/Qwen3-4B-Thinking-2507-Uncensored-Fixed.Q8_0.gguf": "🤖 mradermacher/Qwen3-4B-Thinking-2507-Uncensored-Fixed-GGUF:Q8_0",
    
    "https://huggingface.co/mradermacher/Qwen3-Short-Story-Instruct-Uncensored-262K-ctx-4B-GGUF/blob/main/Qwen3-Short-Story-Instruct-Uncensored-262K-ctx-4B.Q8_0.gguf": "🤖 mradermacher/Qwen3-Short-Story-Instruct-Uncensored-262K-ctx-4B-GGUF:Q8_0",
    
    "https://huggingface.co/Triangle104/Josiefied-Qwen3-4B-abliterated-v2-Q8_0-GGUF/blob/main/josiefied-qwen3-4b-abliterated-v2-q8_0.gguf": "🤖 Triangle104/Josiefied-Qwen3-4B-abliterated-v2-Q8_0-GGUF",
}


def parse_model_input(model_input: str) -> str:
    """
    解析模型输入，支持多种格式：
    1. 模型 ID: "user/repo:quantization"
    2. HuggingFace URL
    3. 本地文件名: "model.gguf"
    
    Returns:
        标准化的模型标识符
    """
    model_input = model_input.strip()
    
    # 如果是 HuggingFace URL，转换为模型 ID
    if model_input.startswith("https://huggingface.co/"):
        if model_input in HUGGINGFACE_URL_MAPPING:
            return HUGGINGFACE_URL_MAPPING[model_input]
        
        # 尝试从 URL 中提取模型信息
        # 格式: https://huggingface.co/user/repo/blob/main/file.gguf
        # 或: https://huggingface.co/user/repo/resolve/main/file.gguf
        parts = model_input.replace("https://huggingface.co/", "").split("/")
        if len(parts) >= 2:
            user = parts[0]
            repo = parts[1]
            
            # 提取量化类型（如果有）
            if len(parts) >= 4:
                filename = parts[-1]
                # 从文件名提取量化类型，如 Q8_0, Q6_K 等
                import re
                quant_match = re.search(r'\.(Q\d+_[0K]|Q\d+)', filename, re.IGNORECASE)
                if quant_match:
                    quant = quant_match.group(1).upper()
                    return f"{user}/{repo}:{quant}"
            
            return f"{user}/{repo}"
    
    # 直接返回（模型 ID 或本地文件名）
    return model_input


class RemoteAPIConfig:
    """远程 API 配置节点（Nexa/Ollama）"""
    
    @staticmethod
    def get_available_models(base_url="http://127.0.0.1:11434", api_type="nexa"):
        """获取可用模型列表"""
        try:
            # 尝试多个常用端口
            ports_to_try = [40054, 11434, 11435]
            
            # 如果 base_url 中指定了端口，优先使用
            if ':' in base_url.split('//')[-1]:
                try:
                    engine = get_nexa_engine(base_url)
                    if engine.is_service_available():
                        models = engine.get_available_models(force_refresh=False)
                        if models:
                            return models
                except:
                    pass
            
            # 尝试常用端口
            for port in ports_to_try:
                try:
                    test_url = f"http://127.0.0.1:{port}"
                    engine = get_nexa_engine(test_url)
                    if engine.is_service_available():
                        models = engine.get_available_models(force_refresh=False)
                        if models:
                            return models
                except:
                    continue
            
            return ["(请点击刷新按钮)"]
        except:
            return ["(请点击刷新按钮)"]
    
    @classmethod
    def INPUT_TYPES(cls):
        # 获取可用模型列表（会尝试多个端口）
        available_models = cls.get_available_models()
        
        return {
            "required": {
                "base_url": ("STRING", {
                    "default": "http://127.0.0.1:11434",
                    "multiline": False,
                    "tooltip": "API 服务地址（例如：http://127.0.0.1:40054）"
                }),
                "api_type": (["Nexa SDK", "Ollama"], {
                    "default": "Ollama",
                    "tooltip": "API 类型"
                }),
                "model": (available_models, {
                    "default": available_models[0] if available_models else "(请点击刷新按钮)",
                    "tooltip": "选择模型（点击刷新按钮更新列表）"
                }),
            },
            "optional": {
                "system_prompt": (IO.STRING, {
                    "default": "",
                    "multiline": True,
                    "tooltip": "系统提示词（可选）"
                }),
            }
        }
    
    RETURN_TYPES = ("TEXT_MODEL",)
    RETURN_NAMES = ("model_config",)
    FUNCTION = "configure_api"
    CATEGORY = "🤖 GGUF-VLM/💬 Text Models"
    
    def configure_api(
        self, 
        base_url: str,
        api_type: str,
        model: str,
        system_prompt: str = ""
    ):
        """配置远程 API"""
        
        # 映射 API 类型
        api_type_map = {
            "Nexa SDK": "nexa",
            "Ollama": "ollama"
        }
        api_key = api_type_map.get(api_type, "nexa")
        
        # 创建或获取引擎
        engine = get_nexa_engine(base_url)
        
        # 检查服务是否可用
        is_available = engine.is_service_available()
        
        if not is_available:
            error_msg = f"⚠️  {api_type} service is not available at {base_url}"
            print(error_msg)
            print(f"   Please make sure the service is running.")
            
            config = {
                "mode": "remote",
                "base_url": base_url,
                "api_type": api_key,
                "model_name": model,
                "system_prompt": system_prompt,
                "service_available": False,
                "error": error_msg
            }
            return (config,)
        
        # 获取可用模型
        available_models = engine.get_available_models(force_refresh=False)
        
        # 确定使用的模型
        if model and model.strip() and not model.startswith("("):
            # 用户选择了有效的模型
            selected_model = model.strip()
            print(f"   使用选择的模型: {selected_model}")
        elif available_models and available_models[0] and not available_models[0].startswith("("):
            # 自动选择第一个可用模型
            selected_model = available_models[0]
            print(f"   自动选择模型: {selected_model}")
        else:
            selected_model = ""
            print(f"   ⚠️  未找到可用模型，请点击刷新按钮")
        
        # 创建配置（使用 TEXT_MODEL 格式，兼容 TextGeneration 节点）
        config = {
            "mode": "remote",
            "base_url": base_url,
            "api_type": api_key,
            "model_name": selected_model,
            "system_prompt": system_prompt,
            "service_available": True,
            "available_models": available_models
        }
        
        print(f"✅ {api_type} configured")
        print(f"   Service URL: {base_url}")
        print(f"   Model: {selected_model}")
        print(f"   Available models: {len(available_models)}")
        
        return (config,)


# RemoteTextGeneration 节点已移除
# 请使用 unified_text_node.py 中的 TextGeneration 节点
# RemoteAPIConfig 现在输出 TEXT_MODEL 类型，可以直接连接到 TextGeneration


class NexaServiceStatus:
    """Nexa SDK 服务状态检查节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        # 获取 LLM 模型目录
        if HAS_PATH_CONFIG:
            default_models_dir = PathConfig.get_llm_models_path()
        else:
            import folder_paths
            default_models_dir = os.path.join(folder_paths.models_dir, "LLM", "GGUF")
            os.makedirs(default_models_dir, exist_ok=True)
        
        return {
            "required": {
                "base_url": ("STRING", {
                    "default": "http://127.0.0.1:11434",
                    "tooltip": "Nexa SDK 服务地址（可配置）"
                }),
                "models_dir": ("STRING", {
                    "default": default_models_dir,
                    "tooltip": "本地模型目录"
                }),
                "refresh": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "刷新模型列表"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("status", "remote_models", "local_models")
    FUNCTION = "check_status"
    CATEGORY = "🤖 GGUF-VLM/🛠️ Tools"
    OUTPUT_NODE = True
    
    def check_status(self, base_url: str, models_dir: str, refresh: bool = False):
        """检查服务状态"""
        
        engine = get_nexa_engine(base_url, models_dir)
        
        # 检查服务是否可用
        is_available = engine.is_service_available()
        
        status_lines = []
        status_lines.append(f"Nexa SDK Service: {base_url}")
        status_lines.append(f"Models Directory: {models_dir}")
        status_lines.append("")
        
        if is_available:
            # 获取远程模型列表
            remote_models = engine.get_available_models(force_refresh=refresh)
            
            status_lines.append(f"✅ Service is AVAILABLE")
            status_lines.append(f"Found {len(remote_models)} remote model(s)")
            
            remote_models_str = "\n".join([f"  - {model}" for model in remote_models]) if remote_models else "  (none)"
        else:
            status_lines.append(f"❌ Service is NOT AVAILABLE")
            status_lines.append("Please make sure the service is running.")
            remote_models_str = "Service unavailable"
        
        # 获取本地模型列表
        local_models = engine.get_local_models()
        status_lines.append(f"Found {len(local_models)} local model(s)")
        
        local_models_str = "\n".join([f"  - {model}" for model in local_models]) if local_models else "  (none)"
        
        status = "\n".join(status_lines)
        
        print(status)
        print("\nRemote models:")
        print(remote_models_str)
        print("\nLocal models:")
        print(local_models_str)
        
        return (status, remote_models_str, local_models_str)


# 节点注册
NODE_CLASS_MAPPINGS = {
    "RemoteAPIConfig": RemoteAPIConfig,
    "NexaServiceStatus": NexaServiceStatus,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RemoteAPIConfig": "🌐 Remote API Config (Nexa/Ollama)",
    "NexaServiceStatus": "📊 Service Status Check",
}
