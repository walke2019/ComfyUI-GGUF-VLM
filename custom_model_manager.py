"""
统一模型管理节点 - 集成所有管理功能
"""

import os
import yaml
from pathlib import Path


class GGUFModelManager:
    """GGUF 模型管理器 - 浏览、添加、列出自定义模型"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "action": (["浏览仓库", "添加模型", "列出模型", "刷新模型列表"], {
                    "default": "浏览仓库",
                    "tooltip": "选择操作"
                }),
                "repo_id": ("STRING", {
                    "default": "username/repo-name-GGUF",
                    "multiline": False,
                    "tooltip": "HuggingFace 仓库 ID"
                }),
            },
            "optional": {
                "model_name": ("STRING", {
                    "default": "My Custom Model",
                    "multiline": False,
                    "tooltip": "模型显示名称（添加模型时需要）"
                }),
                "model_file": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "GGUF 文件名（从浏览结果复制）"
                }),
                "mmproj_file": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "mmproj 文件名（可选）"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result",)
    FUNCTION = "manage_models"
    CATEGORY = "🤖 GGUF-VLM/Management"
    OUTPUT_NODE = True
    
    def manage_models(self, action, repo_id, model_name="", model_file="", mmproj_file=""):
        """统一的模型管理入口"""
        try:
            if action == "浏览仓库":
                return self._browse_repo(repo_id)
            elif action == "添加模型":
                return self._add_model(model_name, repo_id, model_file, mmproj_file)
            elif action == "列出模型":
                return self._list_models()
            elif action == "刷新模型列表":
                return self._refresh_models()
            else:
                return (f"未知操作: {action}",)
        except Exception as e:
            error_msg = f"操作失败: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return (error_msg,)
    
    def _browse_repo(self, repo_id):
        """浏览仓库"""
        from .repo_browser import browse_huggingface_repo, format_file_list
        
        print(f"浏览仓库: {repo_id}")
        result = browse_huggingface_repo(repo_id.strip())
        
        if not result['success']:
            return (f"浏览失败: {result['error']}",)
        
        file_list = format_file_list(result['files'])
        print(file_list)
        
        return (file_list,)
    
    def _add_model(self, model_name, repo_id, model_file, mmproj_file):
        """添加自定义模型"""
        from .gguf_validator import validate_custom_model_config, format_validation_result
        
        if not model_file:
            return ("请先浏览仓库，然后复制模型文件名",)
        
        config = {
            'name': model_name.strip(),
            'repo': repo_id.strip(),
            'file': model_file.strip(),
        }
        
        if mmproj_file.strip():
            config['mmproj'] = mmproj_file.strip()
        
        # 验证
        print("验证模型配置...")
        validation = validate_custom_model_config(config)
        
        if not validation['valid']:
            error_msg = format_validation_result(validation)
            return (error_msg,)
        
        # 保存
        config_path = Path(__file__).parent / "custom_models.yaml"
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
        else:
            data = {}
        
        if 'custom_models' not in data:
            data['custom_models'] = []
        
        # 检查重复
        existing = None
        for i, model in enumerate(data['custom_models']):
            if model.get('repo') == config['repo'] and model.get('file') == config['file']:
                existing = i
                break
        
        if existing is not None:
            data['custom_models'][existing] = config
            action_text = "更新"
        else:
            data['custom_models'].append(config)
            action_text = "添加"
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        # 清除缓存
        try:
            from .nodes import clear_model_cache
            clear_model_cache("custom model added/updated")
        except Exception:
            pass
        
        success_msg = f"成功{action_text}模型: {model_name}\n"
        success_msg += f"仓库: {repo_id}\n"
        success_msg += f"文件: {model_file}\n"
        if mmproj_file:
            success_msg += f"mmproj: {mmproj_file}\n"
        success_msg += f"\n请重新加载节点以查看新模型"
        
        print(success_msg)
        return (success_msg,)
    
    def _list_models(self):
        """列出自定义模型"""
        config_path = Path(__file__).parent / "custom_models.yaml"
        
        if not config_path.exists():
            return ("还没有添加任何自定义模型\n\n使用'浏览仓库'和'添加模型'功能来添加",)
        
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        
        models = data.get('custom_models', [])
        
        if not models:
            return ("还没有添加任何自定义模型",)
        
        output = f"自定义模型列表 ({len(models)} 个):\n\n"
        
        for i, model in enumerate(models, 1):
            output += f"{i}. {model.get('name', 'Unnamed')}\n"
            output += f"   仓库: {model.get('repo', 'N/A')}\n"
            output += f"   文件: {model.get('file', 'N/A')}\n"
            if model.get('mmproj'):
                output += f"   mmproj: {model['mmproj']}\n"
            if model.get('size'):
                output += f"   大小: {model['size']}\n"
            output += "\n"
        
        print(output)
        return (output,)

    def _refresh_models(self):
        """手动刷新模型缓存"""
        try:
            from .nodes import clear_model_cache, MODEL_REGISTRY
            clear_model_cache("manual refresh via manager")
            if MODEL_REGISTRY and hasattr(MODEL_REGISTRY, "reload"):
                try:
                    MODEL_REGISTRY.reload()
                    print("🔄 模型注册表重新加载完成")
                except Exception as registry_err:
                    print(f"⚠️  模型注册表重新加载失败: {registry_err}")
            return ("🔄 模型列表缓存已刷新\n\n请重新打开节点或下拉菜单查看最新状态",)
        except Exception as e:
            error_msg = f"刷新失败: {str(e)}"
            print(error_msg)
            return (error_msg,)


# 注册节点
NODE_CLASS_MAPPINGS = {
    "GGUFModelManager": GGUFModelManager,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GGUFModelManager": "🔧 GGUF Model Manager",
}
