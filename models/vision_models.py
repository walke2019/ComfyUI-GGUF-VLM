"""
Vision Model Configuration - 视觉语言模型配置
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class VisionModelConfig:
    """视觉语言模型配置"""
    
    model_name: str
    model_path: str
    mmproj_path: Optional[str] = None
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
    business_type: str = "image_analysis"
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'model_name': self.model_name,
            'model_path': self.model_path,
            'mmproj_path': self.mmproj_path,
            'n_ctx': self.n_ctx,
            'n_gpu_layers': self.n_gpu_layers,
            'verbose': self.verbose,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'top_k': self.top_k,
            'repeat_penalty': self.repeat_penalty,
            'business_type': self.business_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'VisionModelConfig':
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


class VisionModelPresets:
    """预设的视觉模型配置"""
    
    @staticmethod
    def get_qwen25_vl_3b() -> Dict:
        """Qwen2.5-VL-3B 预设"""
        return {
            'n_ctx': 8192,
            'n_gpu_layers': -1,
            'max_tokens': 512,
            'temperature': 0.7,
            'business_type': 'image_analysis'
        }
    
    @staticmethod
    def get_qwen25_vl_7b() -> Dict:
        """Qwen2.5-VL-7B 预设"""
        return {
            'n_ctx': 8192,
            'n_gpu_layers': -1,
            'max_tokens': 512,
            'temperature': 0.7,
            'business_type': 'image_analysis'
        }
    
    @staticmethod
    def get_qwen3_vl_8b() -> Dict:
        """Qwen3-VL-8B 预设"""
        return {
            'n_ctx': 8192,
            'n_gpu_layers': -1,
            'max_tokens': 1024,
            'temperature': 0.7,
            'business_type': 'image_analysis'
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
            'qwen2.5-vl-3b': VisionModelPresets.get_qwen25_vl_3b(),
            'qwen2.5-vl-7b': VisionModelPresets.get_qwen25_vl_7b(),
            'qwen3-vl-8b': VisionModelPresets.get_qwen3_vl_8b(),
        }
        
        model_name_lower = model_name.lower()
        for key, preset in presets.items():
            if key in model_name_lower:
                return preset
        
        return None
