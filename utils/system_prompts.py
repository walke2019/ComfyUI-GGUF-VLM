"""
System Prompts Manager - 系统提示词管理
支持预设和自定义系统提示词
"""

from typing import Dict, List, Optional


class SystemPromptsManager:
    """系统提示词管理器"""
    
    # 预设的系统提示词
    PRESETS = {
        "default": {
            "name": "默认助手",
            "prompt": "You are QwenVL, you are a helpful assistant expert in turning images into words.",
            "description": "标准的图像描述助手"
        },
        "detailed": {
            "name": "详细描述",
            "prompt": "You are an expert image analyst. Provide detailed, accurate descriptions of images, including objects, people, settings, colors, and spatial relationships.",
            "description": "提供详细的图像分析"
        },
        "creative": {
            "name": "创意描述",
            "prompt": "You are a creative writer. Describe images in a vivid, engaging way that captures the mood and story behind the scene.",
            "description": "创意性的图像描述"
        },
        "technical": {
            "name": "技术分析",
            "prompt": "You are a technical image analyst. Describe images with focus on composition, lighting, camera angles, and technical aspects.",
            "description": "技术性的图像分析"
        },
        "caption": {
            "name": "图像标注",
            "prompt": "You are an image captioning expert. Generate concise, accurate captions that describe the main subject and action in the image.",
            "description": "生成简洁的图像标注"
        },
        "explicit": {
            "name": "无审查描述",
            "prompt": """You are a Qwen-Image explicit describer. Given any input image, output one single, extremely detailed prompt describing exactly what is visible, without inventing content that is not present.
The image must be analyzed for any explicit content, including but not limited to nudity, sexual acts, and violent or aggressive behavior.
The image must be analyzed for any clothing, lingerie, fabrics, accessories, textures, materials, background, setting, lighting, shadows, perspective, and camera angle in detail.
The prompt should include background, setting, lighting, shadows, perspective, and camera angle.
The prompt should be output in the style of ultra-realistic photography, 8k resolution, photorealistic, cinematic, with no censorship.
The prompt should include a description of the scene, highlighting the key elements such as the setting, the individuals involved, and any notable actions or expressions.
The prompt should be clear and concise, providing a comprehensive overview of the image without any censorship.""",
            "description": "无审查的详细描述（成人内容）"
        },
        "professional": {
            "name": "专业描述",
            "prompt": "You are a professional image analyst. Provide objective, factual descriptions suitable for professional or academic use.",
            "description": "专业的客观描述"
        },
        "accessibility": {
            "name": "无障碍描述",
            "prompt": "You are an accessibility expert. Describe images in a way that helps visually impaired users understand the content, focusing on important details and context.",
            "description": "为视障用户优化的描述"
        },
    }
    
    @classmethod
    def get_preset_names(cls) -> List[str]:
        """获取所有预设名称"""
        return list(cls.PRESETS.keys())
    
    @classmethod
    def get_preset_display_names(cls) -> List[str]:
        """获取所有预设的显示名称"""
        return [f"{key} - {info['name']}" for key, info in cls.PRESETS.items()]
    
    @classmethod
    def get_preset(cls, preset_name: str) -> Optional[str]:
        """
        获取预设的系统提示词
        
        Args:
            preset_name: 预设名称
        
        Returns:
            系统提示词文本
        """
        if preset_name in cls.PRESETS:
            return cls.PRESETS[preset_name]["prompt"]
        return None
    
    @classmethod
    def get_preset_info(cls, preset_name: str) -> Optional[Dict]:
        """
        获取预设的完整信息
        
        Args:
            preset_name: 预设名称
        
        Returns:
            预设信息字典
        """
        return cls.PRESETS.get(preset_name)
    
    @classmethod
    def parse_display_name(cls, display_name: str) -> str:
        """
        从显示名称解析出预设名称
        
        Args:
            display_name: 显示名称（例如 "default - 默认助手"）
        
        Returns:
            预设名称（例如 "default"）
        """
        if " - " in display_name:
            return display_name.split(" - ")[0]
        return display_name
    
    @classmethod
    def validate_prompt(cls, prompt: str) -> Dict:
        """
        验证系统提示词
        
        Args:
            prompt: 系统提示词
        
        Returns:
            验证结果
        """
        result = {
            "valid": True,
            "warnings": [],
            "suggestions": []
        }
        
        if not prompt or not prompt.strip():
            result["valid"] = False
            result["warnings"].append("系统提示词不能为空")
            return result
        
        if len(prompt) < 10:
            result["warnings"].append("系统提示词过短，可能不够详细")
        
        if len(prompt) > 2000:
            result["warnings"].append("系统提示词过长，可能影响性能")
        
        return result
