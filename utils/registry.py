"""
Registry Manager - 管理模型注册表
"""

import os
import yaml
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class RegistryManager:
    """模型注册表管理器 - 重构版"""
    
    def __init__(self, config_path: str = None):
        """
        初始化注册表管理器
        
        Args:
            config_path: YAML 配置文件路径
        """
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "..", "model_registry.yaml")
        
        self.config_path = config_path
        self.config = self._load_config()
        self._cache = {}
    
    def _load_config(self) -> dict:
        """加载 YAML 配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"❌ Failed to load registry config: {e}")
            return {}
    
    def get_all_models(self, business_type: str = None) -> List[Dict]:
        """
        获取所有模型列表
        
        Args:
            business_type: 业务类型过滤
        
        Returns:
            模型信息列表
        """
        models = []
        
        for category_key, category_data in self.config.items():
            if not isinstance(category_data, dict) or category_key in ['metadata', 'matching_rules']:
                continue
            
            for series_key, series_data in category_data.items():
                if not isinstance(series_data, dict):
                    continue
                
                series_name = series_data.get('series_name', series_key)
                series_business_type = series_data.get('business_type', 'unknown')
                
                if business_type and series_business_type != business_type:
                    continue
                
                models_list = series_data.get('models', [])
                if not isinstance(models_list, list):
                    continue
                
                for item in models_list:
                    model_info = {
                        'series': series_name,
                        'series_key': series_key,
                        'business_type': series_business_type,
                        'model_name': item['model_name'],
                        'repo': item['repo'],
                        'mmproj': item.get('mmproj'),
                        'mmproj_repo': item.get('mmproj_repo'),
                        'description': item.get('description', ''),
                        'capabilities': item.get('capabilities', []),
                        'variants': item.get('variants', [])
                    }
                    models.append(model_info)
        
        return models
    
    def get_models_by_business_type(self, business_type: str) -> List[Dict]:
        """
        按业务类型获取模型
        
        Args:
            business_type: 业务类型
        
        Returns:
            模型列表
        """
        return self.get_all_models(business_type=business_type)
    
    def get_downloadable_models(self, business_type: str = None) -> List[Tuple[str, Dict]]:
        """
        获取可下载的模型列表（展开所有变体）
        
        Args:
            business_type: 业务类型过滤
        
        Returns:
            [(display_name, model_info), ...] 列表
        """
        downloadable = []
        models = self.get_all_models(business_type)
        
        for model in models:
            for variant in model['variants']:
                display_name = f"[⬇️ {model['series']}] {variant['file']}"
                
                info = {
                    'file': variant['file'],
                    'repo': model['repo'],
                    'mmproj': model['mmproj'],
                    'size': variant.get('size', 'Unknown'),
                    'recommended': variant.get('recommended', False),
                    'series': model['series'],
                    'model_name': model['model_name'],
                    'business_type': model['business_type']
                }
                
                downloadable.append((display_name, info))
        
        return downloadable
    
    def find_model_by_filename(self, filename: str) -> Optional[Dict]:
        """
        根据文件名查找模型信息
        
        Args:
            filename: 模型文件名
        
        Returns:
            模型信息字典
        """
        filename_lower = filename.lower()
        
        models = self.get_all_models()
        for model in models:
            for variant in model['variants']:
                if variant['file'].lower() == filename_lower:
                    return {
                        'file': variant['file'],
                        'repo': model['repo'],
                        'mmproj': model['mmproj'],
                        'mmproj_repo': model.get('mmproj_repo'),
                        'series': model['series'],
                        'model_name': model['model_name'],
                        'business_type': model['business_type']
                    }
        
        return None
    
    def smart_match_mmproj(self, model_filename: str) -> Optional[str]:
        """
        智能匹配模型对应的 mmproj 文件
        
        Args:
            model_filename: 模型文件名
        
        Returns:
            mmproj 文件名
        """
        if 'mmproj' in model_filename.lower():
            return None
        
        # 精确匹配
        model_info = self.find_model_by_filename(model_filename)
        if model_info and model_info.get('mmproj'):
            return model_info['mmproj']
        
        # 使用匹配规则
        matching_rules = self.config.get('matching_rules', {}).get('patterns', [])
        filename_lower = model_filename.lower()
        
        for rule in matching_rules:
            pattern = rule.get('pattern', '')
            if re.search(pattern, filename_lower):
                series_key = rule.get('series')
                model_name = rule.get('model')
                
                models = self.get_all_models()
                for model in models:
                    if model['series_key'] == series_key and model['model_name'] == model_name:
                        return model.get('mmproj')
        
        return None
    
    def get_model_download_info(self, filename: str) -> Optional[Dict]:
        """
        获取模型下载信息
        
        Args:
            filename: 模型文件名
        
        Returns:
            下载信息字典
        """
        clean_filename = re.sub(r'^\[⬇️.*?\]\s*', '', filename)
        
        model_info = self.find_model_by_filename(clean_filename)
        if not model_info:
            return None
        
        return {
            'filename': clean_filename,
            'repo': model_info['repo'],
            'mmproj': model_info.get('mmproj'),
            'mmproj_repo': model_info.get('mmproj_repo'),
            'url': f"https://huggingface.co/{model_info['repo']}/resolve/main/{clean_filename}"
        }
    
    def get_recommendations(self, level: str = 'balanced') -> Optional[str]:
        """
        获取推荐模型
        
        Args:
            level: 推荐级别
        
        Returns:
            推荐模型名称
        """
        return self.config.get('metadata', {}).get('recommendations', {}).get(level)
    
    def get_business_types(self) -> List[str]:
        """获取所有支持的业务类型"""
        return self.config.get('metadata', {}).get('supported_business_types', [])
    
    def reload(self):
        """重新加载配置文件"""
        self.config = self._load_config()
        self._cache.clear()
        print("🔄 Registry reloaded")
