"""
System Prompt Configuration Node - 系统提示词配置节点
"""

import sys
from pathlib import Path

# 添加父目录到路径
module_path = Path(__file__).parent.parent
if str(module_path) not in sys.path:
    sys.path.insert(0, str(module_path))

try:
    from utils.system_prompts import SystemPromptsManager
    from config.node_definitions import SYSTEM_PROMPT_INPUT
except ImportError:
    from ..utils.system_prompts import SystemPromptsManager
    from ..config.node_definitions import SYSTEM_PROMPT_INPUT


class SystemPromptConfig:
    """系统提示词配置节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        preset_options = SystemPromptsManager.get_preset_display_names()
        
        return {
            "required": {
                "preset": (
                    ["custom"] + preset_options,
                    {
                        "default": preset_options[0],
                        "tooltip": "🤖 选择预设的系统提示词或使用自定义"
                    }
                ),
                "custom_prompt": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "tooltip": "🤖 当选择 'custom' 时使用的自定义系统提示词"
                    }
                ),
            },
            "optional": {
                "enable_system_prompt": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "🤖 是否启用系统提示词"
                    }
                ),
            }
        }
    
    RETURN_TYPES = ("STRING", "BOOLEAN")
    RETURN_NAMES = ("system_prompt", "enabled")
    FUNCTION = "configure"
    CATEGORY = "🤖 GGUF-Fusion/Config"
    
    def configure(self, preset, custom_prompt, enable_system_prompt=True):
        """
        配置系统提示词
        
        Args:
            preset: 预设选择
            custom_prompt: 自定义提示词
            enable_system_prompt: 是否启用
        
        Returns:
            (system_prompt, enabled)
        """
        if not enable_system_prompt:
            return ("", False)
        
        if preset == "custom":
            # 使用自定义提示词
            if not custom_prompt or not custom_prompt.strip():
                print("⚠️  Custom prompt is empty, using default")
                prompt = SystemPromptsManager.get_preset("default")
            else:
                prompt = custom_prompt.strip()
                # 验证自定义提示词
                validation = SystemPromptsManager.validate_prompt(prompt)
                if not validation["valid"]:
                    print(f"⚠️  Custom prompt validation failed: {validation['warnings']}")
                elif validation["warnings"]:
                    for warning in validation["warnings"]:
                        print(f"⚠️  {warning}")
        else:
            # 使用预设
            preset_name = SystemPromptsManager.parse_display_name(preset)
            prompt = SystemPromptsManager.get_preset(preset_name)
            
            if prompt is None:
                print(f"⚠️  Preset '{preset_name}' not found, using default")
                prompt = SystemPromptsManager.get_preset("default")
            else:
                preset_info = SystemPromptsManager.get_preset_info(preset_name)
                print(f"✅ Using preset: {preset_info['name']}")
                print(f"   Description: {preset_info['description']}")
        
        return (prompt, True)


# 导出节点
NODE_CLASS_MAPPINGS = {
    "SystemPromptConfig": SystemPromptConfig,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SystemPromptConfig": "🤖 System Prompt Config",
}
