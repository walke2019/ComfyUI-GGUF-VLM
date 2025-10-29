"""
MMProj Validator - 验证 mmproj 文件兼容性
检测张量不匹配等问题
"""

import os
from typing import Dict, Optional, Tuple


class MMProjValidator:
    """MMProj 文件验证器"""
    
    # 已知的模型和对应的 mmproj 文件映射
    KNOWN_MAPPINGS = {
        # Qwen2.5-VL 系列
        'qwen2.5-vl-7b': {
            'mmproj_patterns': [
                'mmproj-qwen2.5-vl-7b-instruct-f16.gguf',
                'qwen2.5-vl-7b.mmproj-f16.gguf',
            ],
            'vision_encoder': 'qwen2.5-vl',
            'notes': 'Qwen2.5-VL 系列使用相同的视觉编码器'
        },
        'qwen2-vl': {
            'mmproj_patterns': [
                'mmproj-qwen2-vl-7b-instruct-f16.gguf',
            ],
            'vision_encoder': 'qwen2-vl',
            'notes': 'Qwen2-VL 与 Qwen2.5-VL 不兼容'
        },
    }
    
    @staticmethod
    def extract_base_model_name(model_filename: str) -> str:
        """
        提取模型的基础名称（去掉量化后缀和版本号）
        
        Args:
            model_filename: 模型文件名
        
        Returns:
            基础模型名
        """
        import re
        
        # 去掉 .gguf 后缀
        name = model_filename.replace('.gguf', '')
        
        # 去掉量化后缀 (Q8_0, Q4_K_M 等)
        name = re.sub(r'[-.]Q\d+_[KM\d]+$', '', name)
        name = re.sub(r'[-.]Q\d+$', '', name)
        
        # 转换为小写用于匹配
        return name.lower()
    
    @staticmethod
    def check_compatibility(model_filename: str, mmproj_filename: str) -> Dict:
        """
        检查模型和 mmproj 文件的兼容性
        
        Args:
            model_filename: 模型文件名
            mmproj_filename: mmproj 文件名
        
        Returns:
            兼容性检查结果
        """
        result = {
            'compatible': True,
            'confidence': 'unknown',
            'warnings': [],
            'suggestions': []
        }
        
        base_model = MMProjValidator.extract_base_model_name(model_filename)
        base_mmproj = MMProjValidator.extract_base_model_name(mmproj_filename)
        
        # 检查是否是完全匹配
        if base_model in base_mmproj or base_mmproj in base_model:
            result['confidence'] = 'high'
            result['compatible'] = True
            return result
        
        # 检查是否是同一系列
        model_series = base_model.split('-')[0]  # 例如 'qwen2.5'
        mmproj_series = base_mmproj.split('-')[0]
        
        if model_series != mmproj_series:
            result['compatible'] = False
            result['confidence'] = 'low'
            result['warnings'].append(
                f"模型系列不匹配: {model_series} vs {mmproj_series}"
            )
            result['suggestions'].append(
                f"请使用与 {model_series} 系列匹配的 mmproj 文件"
            )
        else:
            result['confidence'] = 'medium'
            result['warnings'].append(
                "模型系列匹配，但具体版本可能不同，可能存在兼容性问题"
            )
        
        return result
    
    @staticmethod
    def suggest_mmproj_for_model(model_filename: str) -> Dict:
        """
        为模型建议合适的 mmproj 文件
        
        Args:
            model_filename: 模型文件名
        
        Returns:
            建议信息
        """
        base_model = MMProjValidator.extract_base_model_name(model_filename)
        
        suggestions = {
            'primary': None,
            'alternatives': [],
            'notes': None
        }
        
        # 检查已知映射
        for known_model, info in MMProjValidator.KNOWN_MAPPINGS.items():
            if known_model in base_model:
                suggestions['primary'] = info['mmproj_patterns'][0]
                suggestions['alternatives'] = info['mmproj_patterns'][1:]
                suggestions['notes'] = info['notes']
                break
        
        # 如果没有找到已知映射，生成通用建议
        if not suggestions['primary']:
            import re
            clean_name = re.sub(r'[-.]Q\d+_[KM\d]+$', '', model_filename.replace('.gguf', ''))
            suggestions['primary'] = f"mmproj-{clean_name.lower()}-f16.gguf"
            suggestions['alternatives'] = [
                f"{clean_name}.mmproj-f16.gguf",
                f"{clean_name}-mmproj.gguf",
            ]
            suggestions['notes'] = "通用建议，请确认与模型匹配"
        
        return suggestions
    
    @staticmethod
    def validate_mmproj_file(mmproj_path: str) -> Dict:
        """
        验证 mmproj 文件的有效性
        
        Args:
            mmproj_path: mmproj 文件路径
        
        Returns:
            验证结果
        """
        result = {
            'valid': False,
            'file_exists': False,
            'file_size': 0,
            'errors': []
        }
        
        if not os.path.exists(mmproj_path):
            result['errors'].append(f"文件不存在: {mmproj_path}")
            return result
        
        result['file_exists'] = True
        
        try:
            stat = os.stat(mmproj_path)
            result['file_size'] = stat.st_size
            
            # 检查文件大小是否合理 (mmproj 通常在几百MB)
            if result['file_size'] < 1024 * 1024:  # < 1MB
                result['errors'].append("文件太小，可能不是有效的 mmproj 文件")
            elif result['file_size'] > 10 * 1024 * 1024 * 1024:  # > 10GB
                result['errors'].append("文件太大，可能不是 mmproj 文件")
            else:
                result['valid'] = True
        
        except Exception as e:
            result['errors'].append(f"读取文件失败: {e}")
        
        return result
