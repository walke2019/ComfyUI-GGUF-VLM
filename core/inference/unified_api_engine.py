"""
统一的 API 引擎
支持 Nexa SDK、Ollama、OpenAI 兼容的 API
"""

import requests
from typing import List, Dict, Any, Optional


class UnifiedAPIEngine:
    """统一的 API 引擎，支持多种 API 后端"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:11434", api_type: str = "ollama"):
        """
        初始化 API 引擎
        
        Args:
            base_url: API 服务地址
            api_type: API 类型 (ollama, nexa, openai)
        """
        self.base_url = base_url.rstrip('/')
        self.api_type = api_type.lower()
        
        # 设置端点
        if self.api_type in ["ollama", "nexa"]:
            self.chat_endpoint = f"{self.base_url}/v1/chat/completions"
            self.models_endpoint = f"{self.base_url}/v1/models"
        elif self.api_type == "openai":
            self.chat_endpoint = f"{self.base_url}/v1/chat/completions"
            self.models_endpoint = f"{self.base_url}/v1/models"
        else:
            # 默认使用 OpenAI 兼容格式
            self.chat_endpoint = f"{self.base_url}/v1/chat/completions"
            self.models_endpoint = f"{self.base_url}/v1/models"
        
        self._available_models = None
    
    def is_service_available(self) -> bool:
        """
        检查服务是否可用
        
        Returns:
            服务是否可用
        """
        try:
            response = requests.get(self.models_endpoint, timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def get_available_models(self, force_refresh: bool = False) -> List[str]:
        """
        获取可用模型列表
        
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
                if 'data' in data:
                    # OpenAI 格式
                    self._available_models = [model['id'] for model in data.get('data', [])]
                elif 'models' in data:
                    # Ollama 格式
                    self._available_models = [model['name'] for model in data.get('models', [])]
                else:
                    self._available_models = []
                
                if not force_refresh:
                    print(f"✅ Found {len(self._available_models)} models from {self.api_type} service")
                
            except Exception as e:
                if not force_refresh:
                    print(f"❌ Failed to fetch models: {e}")
                self._available_models = []
        
        return self._available_models
    
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
        调用 Chat Completion API
        
        Args:
            model: 模型 ID
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
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stream": stream,
        }
        
        # 添加可选参数（不同 API 支持不同参数）
        if top_k is not None:
            payload["top_k"] = top_k
        if repetition_penalty is not None:
            if self.api_type == "ollama":
                payload["repeat_penalty"] = repetition_penalty
            else:
                payload["repetition_penalty"] = repetition_penalty
        
        # 添加其他参数
        payload.update(kwargs)
        
        # 打印调试信息
        print(f"🔍 API Request:")
        print(f"   Type: {self.api_type}")
        print(f"   Endpoint: {self.chat_endpoint}")
        print(f"   Model: {model}")
        print(f"   Messages: {len(messages)} messages")
        
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


# 全局引擎实例缓存
_engine_cache = {}


def get_unified_api_engine(base_url: str = "http://127.0.0.1:11434", api_type: str = "ollama") -> UnifiedAPIEngine:
    """
    获取或创建 API 引擎实例（带缓存）
    
    Args:
        base_url: API 服务地址
        api_type: API 类型
    
    Returns:
        UnifiedAPIEngine 实例
    """
    cache_key = f"{base_url}:{api_type}"
    
    if cache_key not in _engine_cache:
        _engine_cache[cache_key] = UnifiedAPIEngine(base_url, api_type)
    
    return _engine_cache[cache_key]
