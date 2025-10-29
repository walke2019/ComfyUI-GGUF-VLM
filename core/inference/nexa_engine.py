"""
Nexa SDK Inference Engine - 使用 Nexa SDK 服务进行推理
通过 HTTP API 调用本地 Nexa SDK 服务
支持本地模型路径管理、自动下载和与 ComfyUI 的 /models/LLM 目录集成
"""

import requests
import os
import time
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
    
    def wait_for_model_ready(self, model_id: str, max_wait: int = 30, check_interval: int = 2) -> bool:
        """
        等待模型加载完成
        
        Args:
            model_id: 模型 ID
            max_wait: 最大等待时间（秒）
            check_interval: 检查间隔（秒）
        
        Returns:
            模型是否就绪
        """
        print(f"⏳ Waiting for model to be ready...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            # 刷新模型列表
            models = self.get_available_models(force_refresh=True)
            
            if model_id in models:
                print(f"✅ Model is ready!")
                return True
            
            time.sleep(check_interval)
            elapsed = int(time.time() - start_time)
            print(f"   Still waiting... ({elapsed}s)")
        
        print(f"⚠️  Timeout waiting for model")
        return False
    
    def load_model_via_api(self, model_id: str) -> bool:
        """
        通过 Nexa SDK API 加载模型（服务会自动下载）
        
        Args:
            model_id: 模型 ID
        
        Returns:
            是否成功加载
        """
        try:
            print(f"📥 Loading model via Nexa SDK service: {model_id}")
            
            # 尝试直接调用 chat API，服务会自动下载模型
            # 发送一个空请求来触发模型加载
            payload = {
                "model": model_id,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1,
            }
            
            response = requests.post(
                self.chat_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=300  # 5分钟超时，给下载时间
            )
            
            # 如果返回 200，模型已加载
            if response.status_code == 200:
                print(f"✅ Model loaded successfully")
                self._available_models = None  # 刷新缓存
                return True
            
            # 如果返回 400，可能是模型正在加载，等待一下
            elif response.status_code == 400:
                print(f"⏳ Model is loading, waiting for it to be ready...")
                # 等待模型加载完成
                if self.wait_for_model_ready(model_id, max_wait=60):
                    return True
                else:
                    print(f"⚠️  Model loading timeout")
                    return False
            else:
                print(f"⚠️  Model load returned status {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"⚠️  Model loading timeout (may still be downloading in background)")
            # 即使超时，也尝试等待模型出现在列表中
            return self.wait_for_model_ready(model_id, max_wait=30)
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            return False
    
    def ensure_model_available(self, model_id: str, auto_download: bool = True) -> bool:
        """
        确保模型可用（如果不存在则通过服务加载）
        
        Args:
            model_id: 模型 ID
            auto_download: 是否自动下载
        
        Returns:
            模型是否可用
        """
        # 检查是否是本地文件
        if model_id.endswith('.gguf'):
            model_path = self.get_model_path(model_id)
            if os.path.exists(model_path):
                print(f"✅ Local model found: {model_path}")
                return True
            
            if auto_download:
                print(f"⚠️  Local model not found, will try to use remote")
                return False
            
            return False
        
        # 检查远程服务中是否有该模型
        available_models = self.get_available_models(force_refresh=True)
        if model_id in available_models:
            print(f"✅ Model available in Nexa service: {model_id}")
            return True
        
        # 如果不在服务中，尝试通过 API 加载（服务会自动下载）
        if auto_download:
            print(f"📥 Model not in service, attempting to load...")
            return self.load_model_via_api(model_id)
        
        return False
    
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
                if not force_refresh:  # 只在非强制刷新时打印
                    print(f"✅ Found {len(self._available_models)} models in Nexa SDK service")
                
            except Exception as e:
                if not force_refresh:
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
        auto_download: bool = True,
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
            auto_download: 是否自动下载模型
            **kwargs: 其他参数
        
        Returns:
            API 响应
        """
        # 处理模型路径
        original_model = model
        
        # 如果是本地 GGUF 文件路径，需要特殊处理
        if model.endswith('.gguf'):
            if os.path.isabs(model):
                # 绝对路径：Nexa SDK 不支持，需要提取模型名
                model_filename = os.path.basename(model)
                print(f"⚠️  Nexa SDK doesn't support absolute paths")
                print(f"   Using filename: {model_filename}")
                model = model_filename
            elif not os.path.isabs(model):
                # 相对路径/文件名：保持不变
                if self.models_dir:
                    full_path = self.get_model_path(model)
                    print(f"📁 Local GGUF file: {full_path}")
                    # 但发送给 API 时只用文件名
                    model = os.path.basename(model)
        else:
            # 远程模型：确保模型可用
            if auto_download:
                if not self.ensure_model_available(model, auto_download=True):
                    raise RuntimeError(f"Failed to load model: {model}")
        
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
        
        # 打印调试信息
        print(f"🔍 API Request:")
        print(f"   Endpoint: {self.chat_endpoint}")
        print(f"   Model: {payload['model']}")
        print(f"   Messages: {len(payload['messages'])} messages")
        
        try:
            response = requests.post(
                self.chat_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120  # 2分钟超时
            )
            
            # 如果请求失败，打印详细错误信息
            if response.status_code != 200:
                print(f"❌ API Error {response.status_code}:")
                print(f"   Response: {response.text[:500]}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.Timeout:
            raise RuntimeError("Request timeout. The model might be too slow or the service is overloaded.")
        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {e}"
            # 尝试获取响应内容
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.text
                    error_msg += f"\nResponse: {error_detail[:500]}"
                except:
                    pass
            raise RuntimeError(error_msg)
    
    def text_completion(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 512,
        top_p: float = 0.9,
        top_k: Optional[int] = None,
        repetition_penalty: Optional[float] = None,
        auto_download: bool = True,
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
            auto_download: 是否自动下载模型
            **kwargs: 其他参数
        
        Returns:
            API 响应
        """
        # 处理模型路径
        original_model = model
        
        # 如果是本地 GGUF 文件路径，需要特殊处理
        if model.endswith('.gguf'):
            if os.path.isabs(model):
                # 绝对路径：Nexa SDK 不支持，需要提取模型名
                model_filename = os.path.basename(model)
                print(f"⚠️  Nexa SDK doesn't support absolute paths")
                print(f"   Using filename: {model_filename}")
                model = model_filename
            elif not os.path.isabs(model):
                # 相对路径/文件名：保持不变
                if self.models_dir:
                    full_path = self.get_model_path(model)
                    print(f"📁 Local GGUF file: {full_path}")
                    # 但发送给 API 时只用文件名
                    model = os.path.basename(model)
        else:
            # 远程模型：确保模型可用
            if auto_download:
                if not self.ensure_model_available(model, auto_download=True):
                    raise RuntimeError(f"Failed to load model: {model}")
        
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
        auto_download: bool = True,
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
            auto_download: 是否自动下载模型
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
            auto_download=auto_download,
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
