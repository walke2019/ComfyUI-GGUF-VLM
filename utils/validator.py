"""
Model Validator - 验证模型配置和文件
"""

import os
import re
from typing import Dict, List, Optional
from pathlib import Path


class ModelValidator:
    """模型验证器"""
    
    @staticmethod
    def validate_gguf_file(file_path: str) -> Dict:
        """
        验证 GGUF 文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            验证结果字典
        """
        result = {
            'valid': False,
            'exists': False,
            'is_gguf': False,
            'readable': False,
            'size': 0,
            'errors': []
        }
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            result['errors'].append(f"File not found: {file_path}")
            return result
        
        result['exists'] = True
        
        # 检查文件扩展名
        if not file_path.lower().endswith('.gguf'):
            result['errors'].append("File does not have .gguf extension")
            return result
        
        result['is_gguf'] = True
        
        # 检查文件是否可读
        try:
            with open(file_path, 'rb') as f:
                # 读取前几个字节检查 GGUF 魔数
                magic = f.read(4)
                if magic != b'GGUF':
                    result['errors'].append("Invalid GGUF file: magic number mismatch")
                    return result
            
            result['readable'] = True
        except Exception as e:
            result['errors'].append(f"Cannot read file: {e}")
            return result
        
        # 获取文件大小
        try:
            result['size'] = os.path.getsize(file_path)
        except Exception as e:
            result['errors'].append(f"Cannot get file size: {e}")
        
        result['valid'] = True
        return result
    
    @staticmethod
    def validate_model_config(config: Dict) -> Dict:
        """
        验证模型配置
        
        Args:
            config: 模型配置字典
        
        Returns:
            验证结果
        """
        result = {
            'valid': False,
            'errors': [],
            'warnings': []
        }
        
        # 必需字段
        required_fields = ['name', 'repo', 'file']
        for field in required_fields:
            if field not in config or not config[field]:
                result['errors'].append(f"Missing required field: {field}")
        
        if result['errors']:
            return result
        
        # 验证 repo 格式
        repo = config['repo']
        if not re.match(r'^[\w\-\.]+/[\w\-\.]+$', repo):
            result['errors'].append(f"Invalid repo format: {repo} (expected: username/repo-name)")
        
        # 验证文件名格式
        file = config['file']
        if not file.lower().endswith('.gguf'):
            result['errors'].append(f"Invalid file extension: {file} (expected: .gguf)")
        
        # 可选字段验证
        if 'mmproj' in config and config['mmproj']:
            mmproj = config['mmproj']
            if not mmproj.lower().endswith('.gguf'):
                result['warnings'].append(f"mmproj file should have .gguf extension: {mmproj}")
        
        # 如果没有错误，标记为有效
        if not result['errors']:
            result['valid'] = True
        
        return result
    
    @staticmethod
    def validate_repo_id(repo_id: str) -> bool:
        """
        验证 HuggingFace 仓库 ID 格式
        
        Args:
            repo_id: 仓库 ID
        
        Returns:
            是否有效
        """
        pattern = r'^[\w\-\.]+/[\w\-\.]+$'
        return bool(re.match(pattern, repo_id))
    
    @staticmethod
    def check_model_compatibility(model_info: Dict, business_type: str) -> Dict:
        """
        检查模型与业务类型的兼容性
        
        Args:
            model_info: 模型信息
            business_type: 业务类型
        
        Returns:
            兼容性检查结果
        """
        result = {
            'compatible': False,
            'warnings': []
        }
        
        model_business_type = model_info.get('business_type', 'unknown')
        
        if model_business_type == business_type:
            result['compatible'] = True
        elif model_business_type == 'unknown':
            result['compatible'] = True
            result['warnings'].append("Model business type is unknown, compatibility uncertain")
        else:
            result['warnings'].append(
                f"Model is designed for {model_business_type}, but used for {business_type}"
            )
        
        return result
    
    @staticmethod
    def format_validation_result(result: Dict) -> str:
        """
        格式化验证结果为可读字符串
        
        Args:
            result: 验证结果字典
        
        Returns:
            格式化的字符串
        """
        lines = []
        
        if result.get('valid'):
            lines.append("✅ Validation passed")
        else:
            lines.append("❌ Validation failed")
        
        if result.get('errors'):
            lines.append("\nErrors:")
            for error in result['errors']:
                lines.append(f"  - {error}")
        
        if result.get('warnings'):
            lines.append("\nWarnings:")
            for warning in result['warnings']:
                lines.append(f"  - {warning}")
        
        return "\n".join(lines)
