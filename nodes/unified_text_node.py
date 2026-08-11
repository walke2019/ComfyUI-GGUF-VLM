"""
统一的文本生成节点
支持 Local (GGUF)、Ollama API、Nexa SDK API
"""

import os
import sys
import re
from pathlib import Path
from typing import Tuple
from comfy.comfy_types import IO

# 添加父目录到路径
module_path = Path(__file__).parent.parent
if str(module_path) not in sys.path:
    sys.path.insert(0, str(module_path))

try:
    from ..core.model_loader import ModelLoader
    from ..core.inference_engine import get_global_inference_engine
    from ..core.inference.unified_api_engine import get_unified_api_engine
except (ImportError, ValueError):
    from core.model_loader import ModelLoader
    from core.inference_engine import get_global_inference_engine
    from core.inference.unified_api_engine import get_unified_api_engine
import requests


class LocalTextModelLoader:
    """本地 GGUF 文本模型加载器"""

    @staticmethod
    def _filter_text_selectable_models(local_models):
        """Keep all runnable GGUF models, including VL models in text-only mode.

        Only projection/helper files should be hidden from the text loader.
        """
        helper_keywords = ["mmproj", "clip", "projector"]
        return [
            model
            for model in local_models
            if not any(keyword in model.lower() for keyword in helper_keywords)
        ]
    
    @classmethod
    def INPUT_TYPES(cls):
        # 获取本地 GGUF 模型
        loader = ModelLoader()
        local_models = loader.list_models()
        
        # 过滤文本可选模型：VL 主模型也能纯文本运行，只排除 mmproj/clip 等辅助文件
        text_models = cls._filter_text_selectable_models(local_models)
        
        return {
            "required": {
                "model": (text_models if text_models else ["No models found"], {
                    "default": text_models[0] if text_models else "No models found",
                    "tooltip": "本地 GGUF 模型文件"
                }),
                "n_ctx": ("INT", {
                    "default": 8192,
                    "min": 512,
                    "max": 128000,
                    "step": 512,
                    "tooltip": "上下文窗口大小"
                }),
                "device": (["Auto", "GPU", "CPU"], {
                    "default": "Auto",
                    "tooltip": "运行设备 (Auto=自动检测, GPU=全部GPU, CPU=仅CPU)"
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
    FUNCTION = "load_model"
    CATEGORY = "🤖 GGUF-VLM/💬 Text Models"
    
    def load_model(self, model, n_ctx=8192, device="Auto", system_prompt=""):
        """加载本地 GGUF 模型"""
        print(f"\n{'='*80}")
        print(f" 🖥️  Local Text Model Loader")
        print(f"{'='*80}")
        
        if not model or model == "No models found":
            error_msg = "❌ No model selected"
            print(error_msg)
            return ({"error": error_msg},)
        
        # 获取模型路径
        loader = ModelLoader()
        model_path = loader.find_model(model)
        
        if not os.path.exists(model_path):
            error_msg = f"❌ Model file not found: {model_path}"
            print(error_msg)
            return ({"error": error_msg},)
        
        # 根据设备选项设置 n_gpu_layers
        if device == "Auto":
            try:
                import torch
                n_gpu_layers = -1 if torch.cuda.is_available() else 0
                print(f"🔍 Auto device: {'GPU' if n_gpu_layers == -1 else 'CPU'}")
            except:
                n_gpu_layers = -1
        elif device == "GPU":
            n_gpu_layers = -1
            print(f"🎮 Using GPU (all layers)")
        else:  # CPU
            n_gpu_layers = 0
            print(f"💻 Using CPU only")
        
        config = {
            "mode": "local",
            "model_path": model_path,
            "model_name": model,
            "n_ctx": n_ctx,
            "n_gpu_layers": n_gpu_layers,
            "system_prompt": system_prompt
        }
        
        print(f"✅ Local model configured")
        print(f"   Model: {model}")
        print(f"   Path: {model_path}")
        print(f"   Context: {n_ctx}")
        print(f"   Device: {device}")
        print(f"{'='*80}\n")
        
        return (config,)


class RemoteTextModelSelector:
    """远程 API 文本模型选择器"""
    
    @staticmethod
    def get_remote_models(base_url="http://127.0.0.1:11434"):
        """获取远程模型列表（支持 Ollama/Nexa/LM Studio）"""
        try:
            # 尝试多个常用端口
            ports = [11434, 8080, 1234]  # Ollama, Nexa, LM Studio
            for port in ports:
                try:
                    # 尝试 Ollama 格式
                    url = f"http://127.0.0.1:{port}/api/tags"
                    response = requests.get(url, timeout=2)
                    if response.status_code == 200:
                        data = response.json()
                        models = [model['name'] for model in data.get('models', [])]
                        if models:
                            return models
                except:
                    pass
                
                try:
                    # 尝试 OpenAI 兼容格式 (LM Studio/Nexa)
                    url = f"http://127.0.0.1:{port}/v1/models"
                    response = requests.get(url, timeout=2)
                    if response.status_code == 200:
                        data = response.json()
                        if 'data' in data:
                            models = [model['id'] for model in data.get('data', [])]
                            if models:
                                return models
                except:
                    continue
            return ["No models found"]
        except:
            return ["No models found"]
    
    @classmethod
    def INPUT_TYPES(cls):
        remote_models = cls.get_remote_models()
        
        return {
            "required": {
                "base_url": ("STRING", {
                    "default": "http://127.0.0.1:11434",
                    "multiline": False,
                    "tooltip": "API 服务地址（Ollama: 11434, Nexa: 8080, LM Studio: 1234）"
                }),
                "api_type": (["Ollama", "Nexa SDK", "LM Studio", "OpenAI Compatible"], {
                    "default": "Ollama",
                    "tooltip": "API 类型（LM Studio 使用 OpenAI 兼容格式）"
                }),
                "model": (remote_models, {
                    "default": remote_models[0] if remote_models else "No models found",
                    "tooltip": "远程模型名称（自动获取）"
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
    FUNCTION = "select_model"
    CATEGORY = "🤖 GGUF-VLM/💬 Text Models"
    
    def select_model(self, base_url, api_type, model, system_prompt=""):
        """选择远程 API 模型"""
        print(f"\n{'='*80}")
        print(f" 🌐 Remote Text Model Selector")
        print(f"{'='*80}")
        
        api_type_map = {
            "Ollama": "ollama",
            "Nexa SDK": "nexa",
            "LM Studio": "lmstudio",
            "OpenAI Compatible": "openai"
        }
        api_type_key = api_type_map.get(api_type, "ollama")
        
        # 获取 API 引擎
        engine = get_unified_api_engine(base_url, api_type_key)
        
        # 检查服务是否可用
        if not engine.is_service_available():
            error_msg = f"⚠️  {api_type} service is not available at {base_url}"
            print(error_msg)
            print(f"   Please make sure the service is running.")
            
            config = {
                "mode": "remote",
                "base_url": base_url,
                "api_type": api_type_key,
                "service_available": False,
                "system_prompt": system_prompt,
                "error": error_msg
            }
            return (config,)
        
        # 获取可用模型
        available_models = engine.get_available_models(force_refresh=False)
        
        if available_models:
            print(f"✅ Found {len(available_models)} models from {api_type}")
            for i, m in enumerate(available_models[:5], 1):
                print(f"   {i}. {m}")
            if len(available_models) > 5:
                print(f"   ... and {len(available_models) - 5} more")
        else:
            print(f"⚠️  No models found")
        
        # 确定使用的模型
        if model and model != "No models found":
            selected_model = model
        elif available_models:
            selected_model = available_models[0]
        else:
            selected_model = ""
        
        config = {
            "mode": "remote",
            "base_url": base_url,
            "api_type": api_type_key,
            "model_name": selected_model,
            "available_models": available_models,
            "service_available": True,
            "system_prompt": system_prompt
        }
        
        print(f"✅ Remote API configured")
        print(f"   Type: {api_type}")
        print(f"   URL: {base_url}")
        print(f"   Model: {selected_model}")
        print(f"{'='*80}\n")
        
        return (config,)


class TextGeneration:
    """统一的文本生成节点 - 支持本地和远程"""
    
    # 全局推理引擎
    _inference_engine = None
    
    @classmethod
    def _get_engine(cls):
        """获取推理引擎"""
        if cls._inference_engine is None:
            cls._inference_engine = get_global_inference_engine()
        return cls._inference_engine
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_config": ("TEXT_MODEL", {
                    "tooltip": "模型配置（来自 Model Selector）"
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
                    "tooltip": "Top-k 采样"
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
                "prompt": (IO.STRING, {
                    "default": "Hello, how are you?",
                    "multiline": True,
                    "tooltip": "输入提示词"
                }),
            },
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("context", "thinking")
    FUNCTION = "generate"
    CATEGORY = "🤖 GGUF-VLM/💬 Text Models"
    OUTPUT_NODE = True
    
    @staticmethod
    def _extract_thinking(text: str, enable_thinking: bool) -> Tuple[str, str]:
        """
        从输出中提取思考内容
        
        支持多种格式:
        - <think>...</think> (DeepSeek-R1, Qwen3)
        - <thinking>...</thinking>
        - [THINKING]...[/THINKING]
        
        注意：即使禁用 thinking，也会移除空的思考标签和多余空行
        """
        thinking = ""
        final_output = text
        
        # 尝试提取 <think> 标签
        think_pattern = r'<think>(.*?)</think>'
        matches = re.findall(think_pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            thinking = '\n\n'.join(matches)
            final_output = re.sub(think_pattern, '', text, flags=re.DOTALL | re.IGNORECASE).strip()
            return final_output, thinking
        
        # 尝试提取 <thinking> 标签
        thinking_pattern = r'<thinking>(.*?)</thinking>'
        matches = re.findall(thinking_pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            thinking = '\n\n'.join(matches)
            final_output = re.sub(thinking_pattern, '', text, flags=re.DOTALL | re.IGNORECASE).strip()
            return final_output, thinking
        
        # 尝试提取 [THINKING] 标签
        bracket_pattern = r'\[THINKING\](.*?)\[/THINKING\]'
        matches = re.findall(bracket_pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            thinking = '\n\n'.join(matches)
            final_output = re.sub(bracket_pattern, '', text, flags=re.DOTALL | re.IGNORECASE).strip()
            return final_output, thinking
        
        # 没有找到思考标签，但仍需清理空标签和多余空行
        # 移除所有空的思考标签
        final_output = re.sub(r'<think>\s*</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
        final_output = re.sub(r'<thinking>\s*</thinking>', '', final_output, flags=re.DOTALL | re.IGNORECASE)
        final_output = re.sub(r'\[THINKING\]\s*\[/THINKING\]', '', final_output, flags=re.DOTALL | re.IGNORECASE)
        
        # 清理多余的空行（3个或更多连续换行符）
        final_output = re.sub(r'\n{3,}', '\n\n', final_output)
        
        # 清理开头和结尾的空白
        final_output = final_output.strip()
        
        return final_output, "" if not enable_thinking else thinking
    
    def generate(self, model_config, prompt, max_tokens=256, temperature=0.7, top_p=0.9, top_k=40, repetition_penalty=1.1, enable_thinking=False):
        """生成文本"""
        print("\n" + "="*80)
        print(" Unified Text Generation")
        print("="*80)
        
        # 检查配置错误
        if "error" in model_config:
            error_msg = model_config["error"]
            print(f"❌ {error_msg}")
            return (error_msg, "")
        
        mode = model_config.get("mode", "local")
        system_prompt = model_config.get("system_prompt", "")
        
        # 处理思考控制
        if not enable_thinking and system_prompt:
            if 'no_think' not in system_prompt.lower():
                system_prompt = f"{system_prompt} no_think"
                print(f"  🚫 Thinking disabled (added no_think)")
        elif not enable_thinking and not system_prompt:
            system_prompt = "no_think"
            print(f"  🚫 Thinking disabled")
        
        if mode == "local":
            # 本地 GGUF 模式
            return self._generate_local(model_config, prompt, system_prompt, max_tokens, temperature, top_p, top_k, repetition_penalty, enable_thinking)
        else:
            # 远程 API 模式
            return self._generate_remote(model_config, prompt, system_prompt, max_tokens, temperature, top_p, top_k, repetition_penalty, enable_thinking)
    
    def _generate_local(self, model_config, prompt, system_prompt, max_tokens, temperature, top_p, top_k, repetition_penalty, enable_thinking):
        """本地 GGUF 生成"""
        engine = self._get_engine()
        model_path = model_config["model_path"]
        
        print(f"🖥️  Local GGUF Generation")
        print(f"   Model: {model_config['model_name']}")
        print(f"   Path: {model_path}")
        
        # 加载模型（如果未加载）
        if not engine.is_model_loaded(model_path):
            print(f"\n⏳ Loading model...")
            success = engine.load_model(
                model_path=model_path,
                n_ctx=model_config.get('n_ctx', 8192),
                n_gpu_layers=model_config.get('n_gpu_layers', -1),
                verbose=False
            )
            if not success:
                error_msg = "❌ Failed to load model"
                print(error_msg)
                return (error_msg, "")
            print(f"✅ Model loaded")
        
        # 构建完整的 prompt
        full_prompt_parts = []
        
        if system_prompt:
            full_prompt_parts.append(f"System: {system_prompt}")
        
        full_prompt_parts.append(f"User: {prompt}")
        full_prompt_parts.append("Assistant:")
        
        full_prompt = "\n\n".join(full_prompt_parts)
        
        print(f"\n💬 Generating...")
        print(f"   Max tokens: {max_tokens}")
        print(f"   Temperature: {temperature}")
        
        # 设置 stop 序列
        stop_sequences = ["User:", "System:", "\n\n\n", "\n\n##", "\n\nNote:", "\n\nThis "]
        
        try:
            raw_output = engine.generate_text(
                model_path=model_path,
                prompt=full_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repetition_penalty,
                stop=stop_sequences
            )
            
            # 提取思考内容
            final_output, thinking = self._extract_thinking(raw_output, enable_thinking)
            
            # 后处理：合并多段落
            paragraphs = [p.strip() for p in final_output.split('\n\n') if p.strip()]
            if len(paragraphs) > 1:
                final_output = ' '.join(paragraphs)
                print(f"   📝 Merged {len(paragraphs)} paragraphs into one")
            
            final_output = final_output.strip()
            
            if enable_thinking and thinking:
                print(f"   💭 Thinking extracted ({len(thinking)} chars)")
            
            print(f"   ✅ Generated {len(final_output)} characters")
            print("="*80 + "\n")
            
            return (final_output, thinking)
        
        except Exception as e:
            error_msg = f"❌ Generation failed: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return (error_msg, "")
    
    def _generate_remote(self, model_config, prompt, system_prompt, max_tokens, temperature, top_p, top_k, repetition_penalty, enable_thinking):
        """远程 API 生成"""
        base_url = model_config["base_url"]
        api_type = model_config["api_type"]
        model_name = model_config.get("model_name", "")
        
        if not model_config.get("service_available", False):
            error_msg = f"❌ {api_type} service is not available"
            print(error_msg)
            return (error_msg, "")
        
        if not model_name:
            error_msg = "❌ No model specified"
            print(error_msg)
            return (error_msg, "")
        
        print(f"🌐 Remote API Generation")
        print(f"   Type: {api_type}")
        print(f"   URL: {base_url}")
        print(f"   Model: {model_name}")
        
        # 获取 API 引擎
        engine = get_unified_api_engine(base_url, api_type)
        
        # 构建消息列表
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        print(f"\n💬 Generating...")
        print(f"   Max tokens: {max_tokens}")
        print(f"   Temperature: {temperature}")
        print(f"   Messages: {len(messages)}")
        
        try:
            response = engine.chat_completion(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                top_k=top_k,
                repetition_penalty=repetition_penalty
            )
            
            # 提取生成的文本
            raw_output = response['choices'][0]['message']['content']
            
            # 提取思考内容
            final_output, thinking = self._extract_thinking(raw_output, enable_thinking)
            
            # 移除可能的 "Assistant:" 前缀
            for prefix in ["assistant:", "Assistant:", "ASSISTANT:"]:
                if final_output.startswith(prefix):
                    final_output = final_output[len(prefix):].strip()
                    break
            
            final_output = final_output.strip()
            
            if enable_thinking and thinking:
                print(f"   💭 Thinking extracted ({len(thinking)} chars)")
            
            print(f"   ✅ Generated {len(final_output)} characters")
            print("="*80 + "\n")
            
            return (final_output, thinking)
        
        except Exception as e:
            error_msg = f"❌ Generation failed: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return (error_msg, "")


# 节点映射
NODE_CLASS_MAPPINGS = {
    "LocalTextModelLoader": LocalTextModelLoader,
    "RemoteTextModelSelector": RemoteTextModelSelector,
    "TextGeneration": TextGeneration,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LocalTextModelLoader": "🖥️ Local Text Model Loader (GGUF)",
    "RemoteTextModelSelector": "🌐 Remote Text Model Selector",
    "TextGeneration": "🤖 Text Generation",
}
