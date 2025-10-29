"""
Text Model Configuration - 文本生成模型配置
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class TextModelConfig:
    """文本生成模型配置"""
    
    model_name: str
    model_path: str
    n_ctx: int = 8192
    n_gpu_layers: int = -1
    verbose: bool = False
    
    # 推理参数
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    
    # 业务类型
    business_type: str = "text_generation"
    
    # 系统提示词
    system_prompt: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'model_name': self.model_name,
            'model_path': self.model_path,
            'n_ctx': self.n_ctx,
            'n_gpu_layers': self.n_gpu_layers,
            'verbose': self.verbose,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'top_k': self.top_k,
            'repeat_penalty': self.repeat_penalty,
            'business_type': self.business_type,
            'system_prompt': self.system_prompt
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TextModelConfig':
        """从字典创建配置"""
        return cls(**data)
    
    def validate(self) -> Dict:
        """验证配置"""
        errors = []
        
        if not self.model_path:
            errors.append("model_path is required")
        
        if self.n_ctx < 512:
            errors.append("n_ctx must be at least 512")
        
        if self.temperature < 0 or self.temperature > 2:
            errors.append("temperature must be between 0 and 2")
        
        if self.top_p < 0 or self.top_p > 1:
            errors.append("top_p must be between 0 and 1")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }


class TextModelPresets:
    """预设的文本模型配置"""
    
    @staticmethod
    def get_qwen25_7b() -> Dict:
        """Qwen2.5-7B 预设"""
        return {
            'n_ctx': 32768,
            'n_gpu_layers': -1,
            'max_tokens': 2048,
            'temperature': 0.7,
            'business_type': 'text_generation'
        }
    
    @staticmethod
    def get_llama31_8b() -> Dict:
        """Llama 3.1 8B 预设"""
        return {
            'n_ctx': 8192,
            'n_gpu_layers': -1,
            'max_tokens': 2048,
            'temperature': 0.7,
            'business_type': 'text_generation'
        }
    
    @staticmethod
    def get_mistral_7b() -> Dict:
        """Mistral 7B 预设"""
        return {
            'n_ctx': 8192,
            'n_gpu_layers': -1,
            'max_tokens': 2048,
            'temperature': 0.7,
            'business_type': 'text_generation'
        }
    
    @staticmethod
    def get_gemma2_9b() -> Dict:
        """Gemma 2 9B 预设"""
        return {
            'n_ctx': 8192,
            'n_gpu_layers': -1,
            'max_tokens': 2048,
            'temperature': 0.7,
            'business_type': 'text_generation'
        }
    
    @staticmethod
    def get_deepseek_coder() -> Dict:
        """DeepSeek Coder 预设"""
        return {
            'n_ctx': 16384,
            'n_gpu_layers': -1,
            'max_tokens': 4096,
            'temperature': 0.3,  # 代码生成使用较低温度
            'business_type': 'text_generation',
            'system_prompt': 'You are an expert programmer. Write clean, efficient, and well-documented code.'
        }
    
    @staticmethod
    def get_phi3_mini() -> Dict:
        """Phi-3 Mini 预设"""
        return {
            'n_ctx': 128000,  # 128K 上下文
            'n_gpu_layers': -1,
            'max_tokens': 2048,
            'temperature': 0.7,
            'business_type': 'text_generation'
        }
    
    @staticmethod
    def get_preset(model_name: str) -> Optional[Dict]:
        """
        根据模型名称获取预设
        
        Args:
            model_name: 模型名称
        
        Returns:
            预设配置字典
        """
        presets = {
            'qwen2.5': TextModelPresets.get_qwen25_7b(),
            'llama-3.1': TextModelPresets.get_llama31_8b(),
            'llama-3.2': TextModelPresets.get_llama31_8b(),
            'mistral': TextModelPresets.get_mistral_7b(),
            'gemma-2': TextModelPresets.get_gemma2_9b(),
            'deepseek-coder': TextModelPresets.get_deepseek_coder(),
            'deepseek-v2': TextModelPresets.get_qwen25_7b(),
            'phi-3': TextModelPresets.get_phi3_mini(),
        }
        
        model_name_lower = model_name.lower()
        for key, preset in presets.items():
            if key in model_name_lower:
                return preset
        
        # 默认配置
        return {
            'n_ctx': 8192,
            'n_gpu_layers': -1,
            'max_tokens': 2048,
            'temperature': 0.7,
            'business_type': 'text_generation'
        }
