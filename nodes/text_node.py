"""
Text Generation Node - 文本生成节点
"""

import os
import sys
from pathlib import Path

# 添加父目录到路径
module_path = Path(__file__).parent.parent
if str(module_path) not in sys.path:
    sys.path.insert(0, str(module_path))

try:
    from core.model_loader import ModelLoader
    from core.inference_engine import InferenceEngine
    from core.cache_manager import CacheManager
    from utils.registry import RegistryManager
    from utils.downloader import FileDownloader
    from models.text_models import TextModelConfig, TextModelPresets
except ImportError as e:
    print(f"[ComfyUI-GGUF-VisionLM] Import error in text_node: {e}")
    # 尝试相对导入
    from ..core.model_loader import ModelLoader
    from ..core.inference_engine import InferenceEngine
    from ..core.cache_manager import CacheManager
    from ..utils.registry import RegistryManager
    from ..utils.downloader import FileDownloader
    from ..models.text_models import TextModelConfig, TextModelPresets


class TextModelLoader:
    """文本模型加载器节点"""
    
    # 全局实例
    _model_loader = None
    _cache_manager = None
    _registry = None
    
    @classmethod
    def _get_instances(cls):
        """获取全局实例"""
        if cls._model_loader is None:
            cls._model_loader = ModelLoader()
        if cls._cache_manager is None:
            cls._cache_manager = CacheManager()
        if cls._registry is None:
            cls._registry = RegistryManager()
        return cls._model_loader, cls._cache_manager, cls._registry
    
    @classmethod
    def INPUT_TYPES(cls):
        loader, cache, registry = cls._get_instances()
        
        # 获取本地模型
        all_local_models = loader.list_models()
        
        # 过滤本地模型：只显示文本生成类型的模型
        local_models = []
        for model_file in all_local_models:
            model_info = registry.find_model_by_filename(model_file)
            # 如果找到模型信息且是文本生成类型，或者找不到信息（未知模型，保留）
            if model_info is None or model_info.get('business_type') == 'text_generation':
                local_models.append(model_file)
        
        # 获取可下载的文本模型
        downloadable = registry.get_downloadable_models(business_type='text_generation')
        downloadable_names = [name for name, _ in downloadable]
        
        # 合并列表
        all_models = local_models + downloadable_names
        
        if not all_models:
            all_models = ["No models found"]
        
        return {
            "required": {
                "model": (all_models, {
                    "default": all_models[0] if all_models else "No models found",
                    "tooltip": "选择文本生成模型"
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
                "system_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "系统提示词（可选）"
                }),
            }
        }
    
    RETURN_TYPES = ("TEXT_MODEL",)
    RETURN_NAMES = ("model",)
    FUNCTION = "load_model"
    CATEGORY = "GGUF-VisionLM/Text"
    
    def load_model(self, model, n_ctx=8192, device="Auto", system_prompt=""):
        """加载文本模型"""
        loader, cache, registry = self._get_instances()
        
        # 根据设备选项设置 n_gpu_layers
        if device == "Auto":
            # 自动检测：如果有 GPU 则全部使用，否则 CPU
            try:
                import torch
                n_gpu_layers = -1 if torch.cuda.is_available() else 0
                print(f"🔍 Auto device: {'GPU' if n_gpu_layers == -1 else 'CPU'}")
            except:
                n_gpu_layers = -1  # 默认尝试 GPU
        elif device == "GPU":
            n_gpu_layers = -1
            print(f"🎮 Using GPU (all layers)")
        else:  # CPU
            n_gpu_layers = 0
            print(f"💻 Using CPU only")
        
        # 检查是否需要下载
        if model.startswith("[⬇️"):
            print(f"📥 Model needs to be downloaded: {model}")
            download_info = registry.get_model_download_info(model)
            
            if download_info:
                downloader = FileDownloader()
                model_dir = loader.model_dirs[0]
                
                downloaded_path = downloader.download_from_huggingface(
                    repo_id=download_info['repo'],
                    filename=download_info['filename'],
                    dest_dir=model_dir
                )
                
                if downloaded_path:
                    model = download_info['filename']
                    cache.clear("new model downloaded")
                else:
                    raise RuntimeError(f"Failed to download model: {model}")
            else:
                raise ValueError(f"Cannot find download info for: {model}")
        
        # 查找模型路径
        model_path = loader.find_model(model)
        if not model_path:
            raise FileNotFoundError(f"Model not found: {model}")
        
        # 应用预设配置
        preset = TextModelPresets.get_preset(model)
        if preset:
            print(f"📋 Applying preset for {model}")
            if n_ctx == 8192:  # 如果是默认值，使用预设
                n_ctx = preset.get('n_ctx', n_ctx)
        
        # 创建配置
        config = TextModelConfig(
            model_name=model,
            model_path=model_path,
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
            system_prompt=system_prompt if system_prompt else None
        )
        
        # 验证配置
        validation = config.validate()
        if not validation['valid']:
            raise ValueError(f"Invalid config: {validation['errors']}")
        
        print(f"✅ Text model loaded: {model}")
        
        return (config.to_dict(),)


class TextGenerationNode:
    """文本生成节点"""
    
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
                "model": ("TEXT_MODEL", {
                    "tooltip": "文本模型配置"
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
                    "tooltip": "Top-k 采样"
                }),
                "repeat_penalty": ("FLOAT", {
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
                    "tooltip": "对话历史（可选）"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("context", "thinking")
    FUNCTION = "generate"
    CATEGORY = "GGUF-VisionLM/Text"
    OUTPUT_NODE = True
    
    @staticmethod
    def _extract_thinking(text: str, enable_thinking: bool) -> tuple:
        """
        从输出中提取思考内容
        
        支持多种格式:
        1. <think>...</think> (DeepSeek-R1)
        2. <thinking>...</thinking>
        3. [THINKING]...[/THINKING]
        
        Returns:
            (final_output, thinking_content)
        """
        if not enable_thinking:
            return text, ""
        
        import re
        
        # 模式 1: <think>...</think>
        think_pattern = r'<think>(.*?)</think>'
        matches = re.findall(think_pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            thinking = '\n\n'.join(matches)
            # 移除思考标签，保留最终答案
            final_output = re.sub(think_pattern, '', text, flags=re.DOTALL | re.IGNORECASE).strip()
            return final_output, thinking
        
        # 模式 2: <thinking>...</thinking>
        thinking_pattern = r'<thinking>(.*?)</thinking>'
        matches = re.findall(thinking_pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            thinking = '\n\n'.join(matches)
            final_output = re.sub(thinking_pattern, '', text, flags=re.DOTALL | re.IGNORECASE).strip()
            return final_output, thinking
        
        # 模式 3: [THINKING]...[/THINKING]
        bracket_pattern = r'\[THINKING\](.*?)\[/THINKING\]'
        matches = re.findall(bracket_pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            thinking = '\n\n'.join(matches)
            final_output = re.sub(bracket_pattern, '', text, flags=re.DOTALL | re.IGNORECASE).strip()
            return final_output, thinking
        
        # 没有找到思考标记，返回原文
        return text, ""
    
    def generate(self, model, prompt, max_tokens=512, temperature=0.7, top_p=0.9, top_k=40, repeat_penalty=1.1, enable_thinking=False, conversation_history=""):
        """生成文本"""
        engine = self._get_engine()
        
        model_path = model['model_path']
        
        # 加载模型（如果未加载）
        if not engine.is_model_loaded(model_path):
            print(f" Loading model into memory...")
            success = engine.load_model(
                model_path=model_path,
                n_ctx=model.get('n_ctx', 8192),
                n_gpu_layers=model.get('n_gpu_layers', -1),
                verbose=model.get('verbose', False)
            )
            
            if not success:
                raise RuntimeError(f"Failed to load model: {model_path}")
        
        # 处理系统提示词和思考控制
        system_prompt_text = model.get('system_prompt', '')
        
        # 如果禁用思考，添加 no_think 到系统提示词
        if not enable_thinking:
            if system_prompt_text:
                # 检查是否已经有 no_think
                if 'no_think' not in system_prompt_text.lower():
                    system_prompt_text = f"{system_prompt_text} no_think"
            else:
                # 如果没有系统提示词但禁用思考，创建一个
                system_prompt_text = "no_think"
        
        # 构建完整提示词
        full_prompt_parts = []
        
        # 1. 系统提示词（如果有）
        if system_prompt_text:
            full_prompt_parts.append(f"System: {system_prompt_text}")
        
        # 2. 对话历史（如果有）
        if conversation_history:
            full_prompt_parts.append(conversation_history)
        
        # 3. 当前用户输入
        full_prompt_parts.append(f"User: {prompt}")
        full_prompt_parts.append("Assistant:")
        
        full_prompt = "\n\n".join(full_prompt_parts)
        
        print(f"🤖 Generating text...")
        print(f"📝 Prompt preview: {full_prompt[:150]}...")
        if not enable_thinking:
            print(f"🚫 Thinking disabled (no_think in system prompt)")
        
        # 生成文本
        try:
            raw_output = engine.generate_text(
                model_path=model_path,
                prompt=full_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repeat_penalty
            )
            
            # 提取思考内容
            final_output, thinking = self._extract_thinking(raw_output, enable_thinking)
            
            if enable_thinking and thinking:
                print(f" Thinking process extracted ({len(thinking)} chars)")
            
            return (final_output, thinking)
        
        except Exception as e:
            error_msg = f"Generation failed: {str(e)}"
            print(f" {error_msg}")
            return (error_msg, "")


# 节点注册
NODE_CLASS_MAPPINGS = {
    "TextModelLoader": TextModelLoader,
    "TextGenerationNode": TextGenerationNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextModelLoader": "📝 Text Model Loader",
    "TextGenerationNode": "🤖 Text Generation",
}
