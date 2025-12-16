"""
统一的 API 引擎
支持 Nexa SDK、Ollama、LM Studio、OpenAI 兼容的 API
"""

import requests
from typing import List, Dict, Any, Optional


class UnifiedAPIEngine:
    """统一的 API 引擎，支持多种 API 后端"""
    
    # 默认端口映射
    DEFAULT_PORTS = {
        "ollama": 11434,
        "nexa": 8080,
        "lmstudio": 1234,
        "openai": 1234,  # 默认使用 LM Studio 端口
    }
    
    def __init__(self, base_url: str = "http://127.0.0.1:11434", api_type: str = "ollama"):
        """
        初始化 API 引擎
        
        Args:
            base_url: API 服务地址
            api_type: API 类型 (ollama, nexa, lmstudio, openai)
        """
        self.base_url = base_url.rstrip('/')
        self.api_type = api_type.lower()
        
        # 设置端点 - 所有类型都使用 OpenAI 兼容格式
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
            response = requests.get(self.models_endpoint, timeout=3)
            return response.status_code == 200
        except:
            # LM Studio 可能需要更长的响应时间
            if self.api_type == "lmstudio":
                try:
                    # 尝试直接访问根路径
                    response = requests.get(self.base_url, timeout=3)
                    return response.status_code in [200, 404]  # LM Studio 根路径可能返回 404
                except:
                    pass
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
                
            except Exception as e:
                if not force_refresh:
                    print(f"❌ Failed to fetch models: {e}")
                self._available_models = []
        
        return self._available_models
    
    def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 512,
        top_p: float = 0.9,
        top_k: Optional[int] = None,
        repetition_penalty: Optional[float] = None,
        stream: bool = False,
        timeout: int = 300,  # 默认 5 分钟超时（视觉模型需要更长时间）
        **kwargs
    ) -> Dict[str, Any]:
        """
        调用 Chat Completion API（支持文本和视觉模型）
        
        Args:
            model: 模型 ID
            messages: 消息列表，支持两种格式：
                - 文本: [{"role": "user", "content": "..."}]
                - 视觉: [{"role": "user", "content": [
                    {"type": "text", "text": "..."},
                    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
                  ]}]
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
            # LM Studio 不支持 top_k，跳过
            if self.api_type not in ["lmstudio"]:
                payload["top_k"] = top_k
        
        if repetition_penalty is not None:
            if self.api_type == "ollama":
                payload["repeat_penalty"] = repetition_penalty
            elif self.api_type == "lmstudio":
                # LM Studio 使用 frequency_penalty 和 presence_penalty
                # 将 repetition_penalty 转换为这两个参数
                penalty = (repetition_penalty - 1.0) * 2  # 转换范围
                payload["frequency_penalty"] = min(max(penalty, 0), 2)
                payload["presence_penalty"] = min(max(penalty * 0.5, 0), 2)
            else:
                payload["repetition_penalty"] = repetition_penalty
        
        # 添加其他参数
        payload.update(kwargs)
        
        try:
            response = requests.post(
                self.chat_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=timeout  # 使用传入的超时参数
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
