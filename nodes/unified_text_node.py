"""
统一的文本生成节点
支持 Local (GGUF)、Ollama API、Nexa SDK API
"""

import os
import sys
import re
from pathlib import Path
from typing import Tuple

# 添加父目录到路径
module_path = Path(__file__).parent.parent
if str(module_path) not in sys.path:
    sys.path.insert(0, str(module_path))

from core.model_loader import ModelLoader
from core.inference_engine import InferenceEngine
from core.inference.unified_api_engine import get_unified_api_engine


class UnifiedTextModelSelector:
    """统一的文本模型选择器 - 支持本地和远程 API"""
    
    @classmethod
    def INPUT_TYPES(cls):
        # 获取本地 GGUF 模型
        loader = ModelLoader()
        local_models = loader.list_models()
        
        # 过滤文本模型
        vision_keywords = ['llava', 'vision', 'vl', 'multimodal', 'mm', 'clip', 'qwen-vl', 'qwen2-vl']
        text_models = [m for m in local_models if not any(kw in m.lower() for kw in vision_keywords)]
        
        return {
            "required": {
                "mode": (["Local (GGUF)", "Remote (API)"], {
                    "default": "Local (GGUF)",
                    "tooltip": "模型运行模式：本地 GGUF 文件或远程 API 服务"
                }),
            },
            "optional": {
                # Local 模式参数
                "local_model": (text_models if text_models else ["No models found"], {
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
                "n_gpu_layers": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 100,
                    "step": 1,
                    "tooltip": "GPU 层数（-1 表示全部）"
                }),
                # Remote 模式参数
                "base_url": ("STRING", {
                    "default": "http://127.0.0.1:11434",
                    "multiline": False,
                    "tooltip": "API 服务地址"
                }),
                "api_type": (["Ollama", "Nexa SDK", "OpenAI Compatible"], {
                    "default": "Ollama",
                    "tooltip": "API 类型"
                }),
                "remote_model": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "远程模型名称（留空则自动获取）"
                }),
                "refresh_models": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "刷新远程模型列表"
                }),
                # 通用参数
                "system_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "系统提示词（可选）"
                }),
            }
        }
    
    RETURN_TYPES = ("TEXT_MODEL",)
    RETURN_NAMES = ("model_config",)
    FUNCTION = "select_model"
    CATEGORY = "GGUF-FX/Text"
    OUTPUT_NODE = True
    
    def select_model(
        self,
        mode: str,
        local_model: str = "",
        n_ctx: int = 8192,
        n_gpu_layers: int = -1,
        base_url: str = "http://127.0.0.1:11434",
        api_type: str = "Ollama",
        remote_model: str = "",
        refresh_models: bool = False,
        system_prompt: str = ""
    ):
        """选择模型并返回配置"""
        
        print(f"\n{'='*80}")
        print(f" Unified Text Model Selector")
        print(f"{'='*80}")
        print(f"Mode: {mode}")
        
        if mode == "Local (GGUF)":
            # 本地模式
            if not local_model or local_model == "No models found":
                error_msg = "❌ No local model selected"
                print(error_msg)
                return ({"error": error_msg},)
            
            # 获取模型路径
            loader = ModelLoader()
            model_path = loader.get_model_path(local_model)
            
            if not os.path.exists(model_path):
                error_msg = f"❌ Model file not found: {model_path}"
                print(error_msg)
                return ({"error": error_msg},)
            
            config = {
                "mode": "local",
                "model_path": model_path,
                "model_name": local_model,
                "n_ctx": n_ctx,
                "n_gpu_layers": n_gpu_layers,
                "system_prompt": system_prompt
            }
            
            print(f"✅ Local model configured")
            print(f"   Path: {model_path}")
            print(f"   Context: {n_ctx}")
            print(f"   GPU Layers: {n_gpu_layers}")
            
        else:
            # 远程 API 模式
            api_type_map = {
                "Ollama": "ollama",
                "Nexa SDK": "nexa",
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
                    "system_prompt": system_prompt
                }
                return (config,)
            
            # 获取可用模型
            available_models = engine.get_available_models(force_refresh=refresh_models)
            
            if available_models:
                print(f"✅ Found {len(available_models)} models from {api_type}")
                for i, model in enumerate(available_models[:5], 1):
                    print(f"   {i}. {model}")
                if len(available_models) > 5:
                    print(f"   ... and {len(available_models) - 5} more")
            else:
                print(f"⚠️  No models found")
            
            # 确定使用的模型
            if remote_model:
                selected_model = remote_model
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


class UnifiedTextGeneration:
    """统一的文本生成节点 - 支持本地和远程"""
    
    # 全局推理引擎
    _inference_engine = None
    
    @classmethod
    def _get_engine(cls):
        """获取推理引擎"""
        if cls._inference_engine is None:
            cls._inference_engine = InferenceEngine()
        return cls._inference_engine
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_config": ("TEXT_MODEL", {
                    "tooltip": "模型配置（来自 Model Selector）"
                }),
                "max_tokens": ("INT", {
                    "default": 256,
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
                "prompt": ("STRING", {
                    "default": "Hello, how are you?",
                    "multiline": True,
                    "tooltip": "输入提示词"
                }),
            },
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("context", "thinking")
    FUNCTION = "generate"
    CATEGORY = "GGUF-FX/Text"
    OUTPUT_NODE = True
    
    @staticmethod
    def _extract_thinking(text: str, enable_thinking: bool) -> Tuple[str, str]:
        """
        从输出中提取思考内容
        
        支持多种格式:
        - <think>...</think> (DeepSeek-R1, Qwen3)
        - <thinking>...</thinking>
        - [THINKING]...[/THINKING]
        """
        if not enable_thinking:
            return text, ""
        
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
        
        # 没有找到思考标签
        return text, ""
    
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
    "UnifiedTextModelSelector": UnifiedTextModelSelector,
    "UnifiedTextGeneration": UnifiedTextGeneration,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "UnifiedTextModelSelector": "🔷 Unified Text Model Selector",
    "UnifiedTextGeneration": "🔷 Unified Text Generation",
}
