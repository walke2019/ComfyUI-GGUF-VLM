"""
远程视觉模型节点
支持 LM Studio、Ollama、Nexa SDK 等 OpenAI 兼容 API 的视觉模型
"""

import os
import base64
import numpy as np
from io import BytesIO
from PIL import Image
from typing import List, Dict, Any, Optional
from comfy.comfy_types import IO

from ..core.backends import OpenAICompatibleVLMBackend
from ..core.inference.unified_api_engine import get_unified_api_engine
import requests


class RemoteVisionModelConfig:
    """远程视觉模型配置节点"""
    
    @staticmethod
    def get_remote_models(base_url="http://127.0.0.1:1234"):
        """获取远程模型列表"""
        try:
            ports = [1234, 11434, 8080]  # LM Studio, Ollama, Nexa
            for port in ports:
                try:
                    # OpenAI 兼容格式
                    url = f"http://127.0.0.1:{port}/v1/models"
                    response = requests.get(url, timeout=2)
                    if response.status_code == 200:
                        data = response.json()
                        if 'data' in data:
                            models = [model['id'] for model in data.get('data', [])]
                            if models:
                                return models
                except:
                    pass
                
                try:
                    # Ollama 格式
                    url = f"http://127.0.0.1:{port}/api/tags"
                    response = requests.get(url, timeout=2)
                    if response.status_code == 200:
                        data = response.json()
                        models = [model['name'] for model in data.get('models', [])]
                        if models:
                            return models
                except:
                    continue
            return ["(请启动 LM Studio 服务)"]
        except:
            return ["(请启动 LM Studio 服务)"]
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base_url": ("STRING", {
                    "default": "http://127.0.0.1:1234",
                    "multiline": False,
                    "tooltip": "API 服务地址（LM Studio: 1234, Ollama: 11434, Nexa SDK: 8080）"
                }),
                "api_type": (["LM Studio", "Ollama", "Nexa SDK", "OpenAI Compatible"], {
                    "default": "LM Studio",
                    "tooltip": "API 类型（均使用 OpenAI 兼容格式）"
                }),
                # 使用空元组表示动态列表，由前端 JavaScript 控制
                "model": ((), {
                    "tooltip": "视觉模型名称（点击 🔄 Refresh Models 按钮更新列表）"
                }),
            },
            "optional": {
                "system_prompt": (IO.STRING, {
                    "default": "You are a helpful assistant that describes images accurately and in detail.",
                    "multiline": True,
                    "tooltip": "系统提示词（可选）"
                }),
            }
        }
    
    RETURN_TYPES = ("REMOTE_VISION_MODEL",)
    RETURN_NAMES = ("model_config",)
    FUNCTION = "configure"
    CATEGORY = "🤖 GGUF-VLM/🖼️ Vision Models"
    
    def configure(self, base_url: str, api_type: str, model: str, system_prompt: str = ""):
        """配置远程视觉模型"""
        print(f"\n{'='*80}")
        print(f" 🌐 Remote Vision Model Config")
        print(f"{'='*80}")
        
        api_type_map = {
            "LM Studio": "lmstudio",
            "Ollama": "ollama",
            "Nexa SDK": "nexa",
            "OpenAI Compatible": "openai"
        }
        api_type_key = api_type_map.get(api_type, "lmstudio")
        
        # 获取 API 引擎检查服务
        engine = get_unified_api_engine(base_url, api_type_key)
        service_available = engine.is_service_available()
        
        if not service_available:
            print(f"⚠️  {api_type} 服务不可用: {base_url}")
            print(f"   请确保服务正在运行")
        else:
            print(f"✅ {api_type} 服务已连接")
            print(f"   URL: {base_url}")
            print(f"   Model: {model}")
        
        config = {
            "mode": "remote_vision",
            "base_url": base_url,
            "api_type": api_type_key,
            "model_name": model,
            "system_prompt": system_prompt,
            "service_available": service_available
        }
        
        print(f"{'='*80}\n")
        return (config,)


class RemoteVisionAnalysis:
    """远程视觉分析节点 - 支持 LM Studio 等视觉模型"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_config": ("REMOTE_VISION_MODEL", {
                    "tooltip": "远程视觉模型配置"
                }),
                "prompt": (IO.STRING, {
                    "default": "Describe this image in detail.",
                    "multiline": True,
                    "tooltip": "用户提示词"
                }),
                "max_tokens": ("INT", {
                    "default": 1024,
                    "min": 1,
                    "max": 8192,
                    "step": 1,
                    "tooltip": "最大生成 token 数（-1 表示无限制）"
                }),
                "temperature": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.1,
                    "tooltip": "温度参数"
                }),
                "timeout": ("INT", {
                    "default": 300,
                    "min": 60,
                    "max": 1800,
                    "step": 30,
                    "tooltip": "超时时间（秒）- 视觉模型处理图像需要较长时间，建议 300-600 秒"
                }),
            },
            "optional": {
                "image": ("IMAGE", {
                    "tooltip": "输入图像"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("description",)
    FUNCTION = "analyze"
    CATEGORY = "🤖 GGUF-VLM/🖼️ Vision Models"
    OUTPUT_NODE = True
    
    def analyze(
        self,
        model_config: Dict[str, Any],
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        timeout: int = 300,
        image=None
    ):
        """分析图像"""
        print("\n" + "="*80)
        print(" 🖼️ Remote Vision Analysis")
        print("="*80)
        
        # 检查配置
        if not model_config.get("service_available", False):
            error_msg = f"❌ 服务不可用: {model_config.get('base_url', 'unknown')}"
            print(error_msg)
            return (error_msg,)
        
        # 允许纯文本模式（无图像）
        text_only_mode = (image is None)
        
        base_url = model_config["base_url"]
        api_type = model_config["api_type"]
        model_name = model_config.get("model_name", "")
        system_prompt = model_config.get("system_prompt", "")
        
        print(f"🌐 API: {api_type}")
        print(f"📍 URL: {base_url}")
        print(f"🤖 Model: {model_name}")
        
        # 将图像转换为 base64（如果有图像）
        image_base64 = None
        if not text_only_mode:
            image_base64 = self._image_to_base64(image)
            print(f"📷 图像已编码 (base64)")
        else:
            print(f"📝 纯文本模式（无图像）")
        
        # 获取统一 VLM Backend
        engine = get_unified_api_engine(base_url, api_type)
        backend = OpenAICompatibleVLMBackend(engine)
        image_urls = [] if text_only_mode else [f"data:image/png;base64,{image_base64}"]
        
        if text_only_mode:
            print(f"\n💬 正在生成文本响应...")
        else:
            print(f"\n💬 正在分析图像...")
        print(f"   Prompt: {prompt[:50]}...")
        print(f"   Max tokens: {max_tokens}")
        print(f"   Temperature: {temperature}")
        print(f"   Timeout: {timeout} 秒")
        
        try:
            result = backend.generate(
                model=model_name,
                prompt=prompt,
                image_urls=image_urls,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens if max_tokens > 0 else 4096,
                timeout=timeout  # 使用用户指定的超时时间
            )
            
            print(f"\n✅ 分析完成 ({len(result)} 字符)")
            print(f"   预览: {result[:100]}...")
            print("="*80 + "\n")
            
            return (result,)
        
        except Exception as e:
            error_msg = f"❌ 分析失败: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return (error_msg,)
    
    def _image_to_base64(self, image) -> str:
        """将 ComfyUI 图像张量转换为 base64 字符串"""
        # 转换 tensor 到 numpy
        img_array = image.cpu().numpy()
        
        # 处理批次维度
        if img_array.ndim == 4:
            img_array = img_array[0]  # 取第一张图像
        
        # 转换到 0-255 范围
        img_array = np.clip(255.0 * img_array, 0, 255).astype(np.uint8)
        
        # 创建 PIL Image
        img = Image.fromarray(img_array)
        
        # 转换为 base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        return base64.b64encode(buffer.read()).decode('utf-8')


# 节点注册
NODE_CLASS_MAPPINGS = {
    "RemoteVisionModelConfig": RemoteVisionModelConfig,
    "RemoteVisionAnalysis": RemoteVisionAnalysis,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RemoteVisionModelConfig": "🌐 Remote Vision Model Config (LM Studio/Ollama/Nexa)",
    "RemoteVisionAnalysis": "🖼️ Remote Vision Analysis",
}
