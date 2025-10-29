"""
Nexa SDK Inference Engine - 使用 Nexa SDK 服务进行推理
通过 HTTP API 调用本地 Nexa SDK 服务
支持本地模型路径管理，与 ComfyUI 的 /models/LLM 目录集成
"""

import requests
import os
from typing import Dict, List, Optional, Any


class NexaInferenceEngine:
    """Nexa SDK 推理引擎（通过 HTTP API）"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:11434", models_dir: Optional[str] = None):
        """
        初始化 Nexa 推理引擎
        
        Args:
            base_url: Nexa SDK 服务的基础 URL
            models_dir: 本地模型目录（默认使用 ComfyUI 的 /models/LLM）
        """
        self.base_url = base_url.rstrip('/')
        self.models_endpoint = f"{self.base_url}/v1/models"
        self.chat_endpoint = f"{self.base_url}/v1/chat/completions"
        self.completions_endpoint = f"{self.base_url}/v1/completions"
        
        # 模型目录配置
        self.models_dir = models_dir
        
        # 缓存可用模型列表
        self._available_models = None
    
    def set_models_dir(self, models_dir: str):
        """
        设置模型目录
        
        Args:
            models_dir: 模型目录路径
        """
        self.models_dir = models_dir
        os.makedirs(models_dir, exist_ok=True)
        print(f"📁 Nexa SDK models directory set to: {models_dir}")
    
    def get_models_dir(self) -> Optional[str]:
        """
        获取当前配置的模型目录
        
        Returns:
            模型目录路径
        """
        return self.models_dir
    
    def get_local_models(self) -> List[str]:
        """
        获取本地已下载的 GGUF 模型列表
        
        Returns:
            本地模型文件列表
        """
        if not self.models_dir or not os.path.exists(self.models_dir):
            return []
        
        models = []
        for item in os.listdir(self.models_dir):
            if item.endswith('.gguf'):
                models.append(item)
        
        return sorted(models)
    
    def get_model_path(self, model_name: str) -> str:
        """
        获取模型的完整路径
        
        Args:
            model_name: 模型名称或文件名
        
        Returns:
            模型的完整路径
        """
        if not self.models_dir:
            raise ValueError("Models directory not set. Call set_models_dir() first.")
        
        # 如果已经是完整路径，直接返回
        if os.path.isabs(model_name):
            return model_name
        
        # 否则拼接到模型目录
        return os.path.join(self.models_dir, os.path.basename(model_name))
    
    def get_available_models(self, force_refresh: bool = False) -> List[str]:
        """
        获取 Nexa SDK 服务中可用的模型列表
        
        Args:
            force_refresh: 是否强制刷新缓存
        
        Returns:
            模型 ID 列表
        """
        if self._available_models is None or force_refresh:
            try:
                response = requests.get(self.models_endpoint, timeout=5)
                response.raise_for_status()
                data = response.json()
                
                # 提取模型 ID
                self._available_models = [model['id'] for model in data.get('data', [])]
                print(f"✅ Found {len(self._available_models)} models in Nexa SDK service")
                
            except Exception as e:
                print(f"❌ Failed to fetch models from Nexa SDK: {e}")
                self._available_models = []
        
        return self._available_models
    
    def is_service_available(self) -> bool:
        """
        检查 Nexa SDK 服务是否可用
        
        Returns:
            服务是否可用
        """
        try:
            response = requests.get(self.models_endpoint, timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 512,
        top_p: float = 0.9,
        top_k: Optional[int] = None,
        repetition_penalty: Optional[float] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        聊天补全 API
        
        Args:
            model: 模型 ID 或本地路径
            messages: 消息列表 [{"role": "user", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大生成 token 数
            top_p: Top-p 采样
            top_k: Top-k 采样
            repetition_penalty: 重复惩罚
            stream: 是否流式输出
            **kwargs: 其他参数
        
        Returns:
            API 响应
        """
        # 如果是本地文件名（.gguf），转换为完整路径
        if model.endswith('.gguf') and not os.path.isabs(model):
            if self.models_dir:
                model = self.get_model_path(model)
                print(f"📁 Using local model: {model}")
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stream": stream,
        }
        
        # 添加可选参数
        if top_k is not None:
            payload["top_k"] = top_k
        if repetition_penalty is not None:
            payload["repetition_penalty"] = repetition_penalty
        
        # 添加其他参数
        payload.update(kwargs)
        
        try:
            response = requests.post(
                self.chat_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120  # 2分钟超时
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.Timeout:
            raise RuntimeError("Request timeout. The model might be too slow or the service is overloaded.")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API request failed: {e}")
    
    def text_completion(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 512,
        top_p: float = 0.9,
        top_k: Optional[int] = None,
        repetition_penalty: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        文本补全 API
        
        Args:
            model: 模型 ID 或本地路径
            prompt: 输入提示
            temperature: 温度参数
            max_tokens: 最大生成 token 数
            top_p: Top-p 采样
            top_k: Top-k 采样
            repetition_penalty: 重复惩罚
            **kwargs: 其他参数
        
        Returns:
            API 响应
        """
        # 如果是本地文件名（.gguf），转换为完整路径
        if model.endswith('.gguf') and not os.path.isabs(model):
            if self.models_dir:
                model = self.get_model_path(model)
                print(f"📁 Using local model: {model}")
        
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
        }
        
        # 添加可选参数
        if top_k is not None:
            payload["top_k"] = top_k
        if repetition_penalty is not None:
            payload["repetition_penalty"] = repetition_penalty
        
        # 添加其他参数
        payload.update(kwargs)
        
        try:
            response = requests.post(
                self.completions_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.Timeout:
            raise RuntimeError("Request timeout. The model might be too slow or the service is overloaded.")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API request failed: {e}")
    
    def generate_text(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
        top_p: float = 0.9,
        top_k: Optional[int] = None,
        repetition_penalty: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        生成文本（简化接口）
        
        Args:
            model: 模型 ID 或本地路径
            prompt: 用户输入
            system_prompt: 系统提示词（可选）
            temperature: 温度参数
            max_tokens: 最大生成 token 数
            top_p: Top-p 采样
            top_k: Top-k 采样
            repetition_penalty: 重复惩罚
            **kwargs: 其他参数
        
        Returns:
            生成的文本
        """
        # 构建消息列表
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        # 调用聊天补全 API
        response = self.chat_completion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            top_k=top_k,
            repetition_penalty=repetition_penalty,
            **kwargs
        )
        
        # 提取生成的文本
        try:
            return response['choices'][0]['message']['content']
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Failed to parse response: {e}")
    
    def get_model_info(self, model: str) -> Optional[Dict[str, Any]]:
        """
        获取模型信息
        
        Args:
            model: 模型 ID
        
        Returns:
            模型信息字典
        """
        try:
            response = requests.get(self.models_endpoint, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            for model_info in data.get('data', []):
                if model_info['id'] == model:
                    return model_info
            
            return None
        
        except Exception as e:
            print(f"❌ Failed to get model info: {e}")
            return None


# 全局引擎实例字典（按 base_url 区分）
_global_nexa_engines = {}


def get_nexa_engine(base_url: str = "http://127.0.0.1:11434", models_dir: Optional[str] = None) -> NexaInferenceEngine:
    """
    获取 Nexa 推理引擎实例（支持多个不同的服务地址）
    
    Args:
        base_url: Nexa SDK 服务的基础 URL
        models_dir: 本地模型目录
    
    Returns:
        NexaInferenceEngine 实例
    """
    global _global_nexa_engines
    
    # 使用 base_url 作为 key
    if base_url not in _global_nexa_engines:
        _global_nexa_engines[base_url] = NexaInferenceEngine(base_url, models_dir)
    
    # 更新模型目录（如果提供）
    if models_dir:
        _global_nexa_engines[base_url].set_models_dir(models_dir)
    
    return _global_nexa_engines[base_url]
