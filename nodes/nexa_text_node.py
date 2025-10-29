"""
Nexa SDK Text Node - 使用 Nexa SDK 服务的文本生成节点
支持本地模型路径管理、自动下载和与 ComfyUI 的 /models/LLM 目录集成
"""

import re
import os
from typing import Tuple

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
    "https://huggingface.co/prithivMLmods/Qwen3-4B-2507-abliterated-GGUF/blob/main/Qwen3-4B-Instruct-2507-abliterated-GGUF/Qwen3-4B-Instruct-2507-abliterated.Q8_0.gguf": 
        "prithivMLmods/Qwen3-4B-2507-abliterated-GGUF:Q8_0",
    
    "https://huggingface.co/mradermacher/Qwen3-4B-Thinking-2507-Uncensored-Fixed-GGUF/resolve/main/Qwen3-4B-Thinking-2507-Uncensored-Fixed.Q8_0.gguf":
        "mradermacher/Qwen3-4B-Thinking-2507-Uncensored-Fixed-GGUF:Q8_0",
    
    "https://huggingface.co/mradermacher/Qwen3-Short-Story-Instruct-Uncensored-262K-ctx-4B-GGUF/blob/main/Qwen3-Short-Story-Instruct-Uncensored-262K-ctx-4B.Q8_0.gguf":
        "mradermacher/Qwen3-Short-Story-Instruct-Uncensored-262K-ctx-4B-GGUF:Q8_0",
    
    "https://huggingface.co/Triangle104/Josiefied-Qwen3-4B-abliterated-v2-Q8_0-GGUF/blob/main/josiefied-qwen3-4b-abliterated-v2-q8_0.gguf":
        "Triangle104/Josiefied-Qwen3-4B-abliterated-v2-Q8_0-GGUF",
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


class NexaModelSelector:
    """Nexa SDK 模型选择器"""
    
    @classmethod
    def INPUT_TYPES(cls):
        # 默认 API 端点
        default_base_url = "http://127.0.0.1:11434"
        
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
                    "default": default_base_url,
                    "tooltip": "Nexa SDK 服务地址（可配置）"
                }),
                "models_dir": ("STRING", {
                    "default": default_models_dir,
                    "tooltip": "本地模型目录（GGUF 文件存放位置）"
                }),
                "model_source": (["Remote (Nexa Service)", "Local (GGUF File)"], {
                    "default": "Remote (Nexa Service)",
                    "tooltip": "模型来源：远程服务或本地文件"
                }),
                "refresh_models": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "刷新模型列表"
                }),
            },
            "optional": {
                "system_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "系统提示词（可选）"
                }),
            }
        }
    
    RETURN_TYPES = ("NEXA_MODEL", "STRING")
    RETURN_NAMES = ("model_config", "available_models")
    FUNCTION = "select_model"
    CATEGORY = "GGUF-VisionLM/Nexa"
    OUTPUT_NODE = True
    
    def select_model(
        self, 
        base_url: str, 
        models_dir: str,
        model_source: str,
        refresh_models: bool = False,
        system_prompt: str = ""
    ):
        """选择模型并返回配置"""
        
        # 创建或获取引擎
        engine = get_nexa_engine(base_url, models_dir)
        
        # 检查服务是否可用
        is_available = engine.is_service_available()
        
        if not is_available:
            error_msg = f"⚠️  Nexa SDK service is not available at {base_url}"
            print(error_msg)
            print("   Please make sure the service is running.")
            
            # 即使服务不可用，也返回配置（用于本地模型）
            config = {
                "base_url": base_url,
                "models_dir": models_dir,
                "model_source": model_source,
                "system_prompt": system_prompt,
                "engine_type": "nexa",
                "service_available": False
            }
            return (config, error_msg)
        
        # 获取可用模型
        available_models_list = []
        
        if model_source == "Remote (Nexa Service)":
            # 远程模型
            remote_models = engine.get_available_models(force_refresh=refresh_models)
            available_models_list.extend([f"[Remote] {m}" for m in remote_models])
        else:
            # 本地模型
            local_models = engine.get_local_models()
            available_models_list.extend([f"[Local] {m}" for m in local_models])
        
        # 格式化输出
        if available_models_list:
            models_text = "\n".join(available_models_list)
            print(f"✅ Found {len(available_models_list)} models")
        else:
            models_text = "⚠️  No models found"
            print(models_text)
        
        # 创建配置
        config = {
            "base_url": base_url,
            "models_dir": models_dir,
            "model_source": model_source,
            "system_prompt": system_prompt,
            "engine_type": "nexa",
            "service_available": True,
            "available_models": available_models_list
        }
        
        print(f"✅ Nexa SDK configured")
        print(f"   Service URL: {base_url}")
        print(f"   Models Dir: {models_dir}")
        print(f"   Source: {model_source}")
        
        return (config, models_text)


class NexaTextGeneration:
    """Nexa SDK 文本生成节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_config": ("NEXA_MODEL", {
                    "tooltip": "Nexa 模型配置（来自 Model Selector）"
                }),
                "preset_model": (PRESET_MODELS, {
                    "default": PRESET_MODELS[0],
                    "tooltip": "预设模型列表（选择或使用自定义）"
                }),
                "custom_model": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "自定义模型 ID（格式: author/model:quant）"
                }),
                "auto_download": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "自动下载模型（使用 nexa pull）"
                }),
                "prompt": ("STRING", {
                    "default": "Hello, how are you?",
                    "multiline": True,
                    "tooltip": "输入提示词"
                }),
                "max_tokens": ("INT", {
                    "default": 512,
                    "min": 1,
                    "max": 8192,
                    "step": 1,
                    "tooltip": "最大生成 token 数"
                }),
                "temperature": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.1,
                    "tooltip": "温度参数（越高越随机）"
                }),
                "top_p": ("FLOAT", {
                    "default": 0.9,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.05,
                    "tooltip": "Top-p 采样"
                }),
                "top_k": ("INT", {
                    "default": 40,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                    "tooltip": "Top-k 采样（0 表示禁用）"
                }),
                "repetition_penalty": ("FLOAT", {
                    "default": 1.1,
                    "min": 1.0,
                    "max": 2.0,
                    "step": 0.1,
                    "tooltip": "重复惩罚"
                }),
                "enable_thinking": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "启用思考模式（支持 DeepSeek-R1, Qwen3-Thinking 等模型）"
                }),
            },
            "optional": {
                "conversation_history": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "对话历史（JSON 格式的消息列表，可选）"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("context", "thinking", "raw_response")
    FUNCTION = "generate"
    CATEGORY = "GGUF-VisionLM/Nexa"
    OUTPUT_NODE = True
    
    @staticmethod
    def _extract_thinking(text: str, enable_thinking: bool) -> Tuple[str, str]:
        """
        从输出中提取思考内容
        
        支持多种格式:
        1. <think>...</think> (Qwen3, DeepSeek-R1)
        2. <thinking>...</thinking>
        3. [THINKING]...[/THINKING]
        
        无论 enable_thinking 是否启用，都会移除 think 标签。
        当 enable_thinking=False 时，不返回 thinking 内容。
        
        Returns:
            (final_output, thinking_content)
        """
        # 模式 1: <think>...</think>
        think_pattern = r'<think>(.*?)</think>'
        matches = re.findall(think_pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            thinking = '\n\n'.join(matches) if enable_thinking else ""
            # 移除思考标签，保留最终答案
            final_output = re.sub(think_pattern, '', text, flags=re.DOTALL | re.IGNORECASE).strip()
            return final_output, thinking
        
        # 模式 2: <thinking>...</thinking>
        thinking_pattern = r'<thinking>(.*?)</thinking>'
        matches = re.findall(thinking_pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            thinking = '\n\n'.join(matches) if enable_thinking else ""
            final_output = re.sub(thinking_pattern, '', text, flags=re.DOTALL | re.IGNORECASE).strip()
            return final_output, thinking
        
        # 模式 3: [THINKING]...[/THINKING]
        bracket_pattern = r'\[THINKING\](.*?)\[/THINKING\]'
        matches = re.findall(bracket_pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            thinking = '\n\n'.join(matches) if enable_thinking else ""
            final_output = re.sub(bracket_pattern, '', text, flags=re.DOTALL | re.IGNORECASE).strip()
            return final_output, thinking
        
        # 没有找到思考标记，返回原文
        return text, ""
    
    def generate(
        self,
        model_config,
        preset_model: str,
        custom_model: str,
        auto_download: bool,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 40,
        repetition_penalty: float = 1.1,
        enable_thinking: bool = False,
        conversation_history: str = ""
    ):
        """生成文本"""
        
        # 获取配置
        base_url = model_config.get('base_url', 'http://127.0.0.1:11434')
        models_dir = model_config.get('models_dir', '/workspace/ComfyUI/models/LLM')
        model_source = model_config.get('model_source', 'Remote (Nexa Service)')
        system_prompt = model_config.get('system_prompt', '')
        
        # 获取引擎
        engine = get_nexa_engine(base_url, models_dir)
        
        # 检查服务是否可用
        if not engine.is_service_available():
            error_msg = f"❌ Nexa SDK service is not available at {base_url}"
            print(error_msg)
            print("   Please make sure the service is running.")
            return (error_msg, "", "")
        
        # 确定使用哪个模型
        if preset_model == "Custom (输入自定义模型)":
            if not custom_model:
                error_msg = "❌ Please specify a custom model"
                print(error_msg)
                return (error_msg, "", "")
            model = parse_model_input(custom_model)
            print(f"📝 Using custom model: {model}")
        else:
            model = preset_model
            print(f"📋 Using preset model: {model}")
        
        # 如果启用自动下载，确保模型可用
        if auto_download and model_source == "Remote (Nexa Service)":
            print(f"🔍 Checking model availability...")
            engine.ensure_model_available(model, auto_download=True)
        
        # Nexa SDK 只支持通过 'nexa pull' 下载的模型
        # 模型格式: author/model-name:quant
        model_id = model
        print(f"🌐 Using Nexa SDK model: {model_id}")
        print(f"💡 Make sure you've run: nexa pull {model_id}")
        
        # 处理思考控制
        if not enable_thinking and system_prompt:
            # 如果禁用思考，添加 no_think 到系统提示词
            if 'no_think' not in system_prompt.lower():
                system_prompt = f"{system_prompt} no_think"
        elif not enable_thinking and not system_prompt:
            system_prompt = "no_think"
        
        # 构建消息列表
        messages = []
        
        # 1. 系统提示词
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 2. 对话历史（如果提供）
        if conversation_history:
            try:
                import json
                history = json.loads(conversation_history)
                if isinstance(history, list):
                    messages.extend(history)
            except:
                # 如果不是 JSON 格式，作为普通文本添加
                messages.append({"role": "user", "content": conversation_history})
        
        # 3. 当前用户输入
        messages.append({"role": "user", "content": prompt})
        
        print(f"🤖 Generating text with Nexa SDK...")
        print(f"   Model: {model_id}")
        print(f"   Source: {model_source}")
        print(f"   Auto-download: {'✅ Enabled' if auto_download else '❌ Disabled'}")
        print(f"   Messages: {len(messages)} messages")
        if not enable_thinking:
            print(f"   🚫 Thinking disabled")
        
        try:
            # 准备参数
            params = {
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": top_p,
                "auto_download": auto_download,
            }
            
            # 只在非零时添加 top_k 和 repetition_penalty
            if top_k > 0:
                params["top_k"] = top_k
            if repetition_penalty > 1.0:
                params["repetition_penalty"] = repetition_penalty
            
            # 调用 API
            response = engine.chat_completion(
                model=model_id,
                messages=messages,
                **params
            )
            
            # 提取生成的文本
            raw_output = response['choices'][0]['message']['content']
            
            # 提取思考内容
            final_output, thinking = self._extract_thinking(raw_output, enable_thinking)
            
            # 清理输出：移除可能的角色前缀
            final_output = final_output.strip()
            for prefix in ["assistant:", "Assistant:", "ASSISTANT:"]:
                if final_output.startswith(prefix):
                    final_output = final_output[len(prefix):].strip()
                    break
            
            if enable_thinking and thinking:
                print(f"   💭 Thinking process extracted ({len(thinking)} chars)")
            
            print(f"   ✅ Generated {len(final_output)} characters")
            
            # 格式化原始响应
            import json
            raw_response = json.dumps(response, indent=2, ensure_ascii=False)
            
            return (final_output, thinking, raw_response)
        
        except Exception as e:
            error_msg = f"❌ Generation failed: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return (error_msg, "", str(e))


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
    CATEGORY = "GGUF-VisionLM/Nexa"
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
    "NexaModelSelector": NexaModelSelector,
    "NexaTextGeneration": NexaTextGeneration,
    "NexaServiceStatus": NexaServiceStatus,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NexaModelSelector": "🔷 Nexa Model Selector",
    "NexaTextGeneration": "🔷 Nexa Text Generation",
    "NexaServiceStatus": "🔷 Nexa Service Status",
}
