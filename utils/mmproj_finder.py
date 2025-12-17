"""
MMProj Finder - 智能查找 mmproj 文件
支持多种命名模式和自动匹配
"""

import os
from pathlib import Path
from typing import Optional, List
import re


class MMProjFinder:
    """MMProj 文件查找器"""
    
    def __init__(self, search_dirs: List[str] = None):
        """
        初始化 MMProj 查找器
        
        Args:
            search_dirs: 搜索目录列表
        """
        self.search_dirs = search_dirs or []
    
    def _pattern_1(self, model):
        """模型名-mmproj.gguf"""
        return model.replace('.gguf', '-mmproj.gguf')
    
    def _pattern_2(self, model):
        """模型名.mmproj.gguf"""
        return model.replace('.gguf', '.mmproj.gguf')
    
    def _pattern_3(self, model):
        """模型名_mmproj.gguf"""
        return model.replace('.gguf', '_mmproj.gguf')
    
    def _pattern_4(self, model):
        """去掉量化后缀-mmproj.gguf"""
        return re.sub(r'-Q\d+_\d+\.gguf$', '-mmproj.gguf', model)
    
    def _pattern_5(self, model):
        """去掉量化后缀.mmproj.gguf"""
        return re.sub(r'\.Q\d+_\d+\.gguf$', '.mmproj.gguf', model)
    
    def _pattern_6(self, model):
        """去掉量化后缀-mmproj.gguf (另一种格式)"""
        return re.sub(r'-Q\d+_\d+\.gguf$', '.mmproj.gguf', model)
    
    def _pattern_7(self, model):
        """mmproj-模型名"""
        return "mmproj-" + model
    
    def _pattern_8(self, model):
        """mmproj_模型名"""
        return "mmproj_" + model
    
    def _pattern_9(self, model):
        """去掉所有量化标记-mmproj.gguf"""
        cleaned = re.sub(r'[-_.]Q\d+_\d+', '', model)
        return cleaned.replace('.gguf', '-mmproj.gguf')
    
    def _pattern_10(self, model):
        """去掉所有量化标记.mmproj.gguf"""
        cleaned = re.sub(r'[-_.]Q\d+_\d+', '', model)
        return cleaned.replace('.gguf', '.mmproj.gguf')
    
    def _pattern_11(self, model):
        """去掉量化-mmproj-f16.gguf"""
        return re.sub(r'-Q\d+_\d+\.gguf$', '-mmproj-f16.gguf', model)
    
    def _pattern_12(self, model):
        """去掉量化.mmproj-f16.gguf"""
        return re.sub(r'\.Q\d+_\d+\.gguf$', '.mmproj-f16.gguf', model)
    
    def _pattern_13(self, model):
        """mmproj-去掉量化-f16.gguf"""
        base = re.sub(r'-Q\d+_\d+\.gguf$', '', model)
        return "mmproj-" + base + "-f16.gguf"
    
    def _pattern_14(self, model):
        """mmproj-去掉量化-f16.gguf (点号版本)"""
        base = re.sub(r'\.Q\d+_\d+\.gguf$', '', model)
        return "mmproj-" + base + "-f16.gguf"
    
    def _pattern_15(self, model):
        """去掉量化-mmproj-f16.gguf (点号分隔)"""
        return re.sub(r'-Q\d+_\d+\.gguf$', '.mmproj-f16.gguf', model)
    
    def _pattern_16(self, model):
        """去掉量化.mmproj-f16.gguf (点号分隔) - 关键模式！"""
        return re.sub(r'\.Q\d+_\d+\.gguf$', '.mmproj-f16.gguf', model)
    
    def _pattern_17(self, model):
        """模型名-mmproj-f16.gguf (直接替换)"""
        return model.replace('.gguf', '.mmproj-f16.gguf')
    
    def _pattern_18(self, model):
        """模型名.mmproj-f16.gguf (直接替换，点号分隔)"""
        return model.replace('.gguf', '.mmproj-f16.gguf')
    
    def _pattern_19(self, model):
        """保留量化后缀-mmproj.gguf (如 Qwen2.5-VL-7B-Instruct-abliterated-Q4_K_M-mmproj.gguf)"""
        return model.replace('.gguf', '-mmproj.gguf')
    
    def _pattern_20(self, model):
        """保留量化后缀-mmproj-F16.gguf (如 Qwen2.5-VL-7B-Instruct-Q8_0-mmproj-F16.gguf)"""
        return model.replace('.gguf', '-mmproj-F16.gguf')
    
    def _pattern_21(self, model):
        """保留量化后缀-mmproj-f16.gguf (小写版本)"""
        return model.replace('.gguf', '-mmproj-f16.gguf')
    
    def _pattern_22(self, model):
        """去掉量化后缀-mmproj-F16.gguf (大写F16)"""
        return re.sub(r'-Q\d+_[KM\d]+\.gguf$', '-mmproj-F16.gguf', model)
    
    def _pattern_23(self, model):
        """去掉量化后缀-mmproj-F16.gguf (大写F16，另一种量化格式)"""
        return re.sub(r'-Q\d+_\d+\.gguf$', '-mmproj-F16.gguf', model)
    
    def find_mmproj(self, model_filename: str, model_dir: str = None) -> Optional[str]:
        """
        查找模型对应的 mmproj 文件
        
        Args:
            model_filename: 模型文件名
            model_dir: 模型所在目录（优先搜索）
        
        Returns:
            mmproj 文件的完整路径，未找到返回 None
        """
        # 构建搜索目录列表
        search_paths = []
        if model_dir:
            search_paths.append(model_dir)
        search_paths.extend(self.search_dirs)
        
        # 生成所有可能的 mmproj 文件名
        possible_names = self._generate_possible_names(model_filename)
        
        # 在所有目录中搜索
        for search_dir in search_paths:
            if not os.path.exists(search_dir):
                continue
            
            for possible_name in possible_names:
                mmproj_path = os.path.join(search_dir, possible_name)
                if os.path.exists(mmproj_path):
                    return mmproj_path
        
        return None
    
    def _generate_possible_names(self, model_filename: str) -> List[str]:
        """生成所有可能的 mmproj 文件名"""
        possible_names = set()
        
        # 应用所有模式
        patterns = [
            self._pattern_1, self._pattern_2, self._pattern_3,
            self._pattern_4, self._pattern_5, self._pattern_6,
            self._pattern_7, self._pattern_8, self._pattern_9,
            self._pattern_10, self._pattern_11, self._pattern_12,
            self._pattern_13, self._pattern_14, self._pattern_15,
            self._pattern_16, self._pattern_17, self._pattern_18,
            self._pattern_19, self._pattern_20, self._pattern_21,
            self._pattern_22, self._pattern_23,
        ]
        
        for pattern in patterns:
            try:
                name = pattern(model_filename)
                if name and name != model_filename:
                    possible_names.add(name)
            except:
                pass
        
        # 添加一些手动规则
        base_name = model_filename.replace('.gguf', '')
        
        # 移除常见的量化后缀
        for suffix in ['-Q8_0', '-Q6_K', '-Q5_K_M', '-Q4_K_M', '-Q4_K_S', '-Q3_K_M', '-Q2_K', '.Q8_0', '.Q6_K', '.Q5_K_M', '.Q4_K_M', '.Q4_K_S', '.Q3_K_M', '.Q2_K']:
            if base_name.endswith(suffix):
                clean_name = base_name[:-len(suffix)]
                # 不带量化后缀的 mmproj 命名
                possible_names.add(clean_name + "-mmproj.gguf")
                possible_names.add(clean_name + ".mmproj.gguf")
                possible_names.add(clean_name + "-mmproj-f16.gguf")
                possible_names.add(clean_name + "-mmproj-F16.gguf")  # 大写 F16
                possible_names.add(clean_name + ".mmproj-f16.gguf")
                possible_names.add(clean_name + ".mmproj-F16.gguf")  # 大写 F16
                possible_names.add("mmproj-" + clean_name + ".gguf")
                possible_names.add("mmproj-" + clean_name + "-f16.gguf")
                possible_names.add("mmproj-" + clean_name + "-F16.gguf")  # 大写 F16
                
                # 带量化后缀的 mmproj 命名 (如 Qwen2.5-VL-7B-Instruct-Q8_0-mmproj-F16.gguf)
                possible_names.add(base_name + "-mmproj.gguf")
                possible_names.add(base_name + "-mmproj-f16.gguf")
                possible_names.add(base_name + "-mmproj-F16.gguf")  # 大写 F16
                possible_names.add(base_name + ".mmproj.gguf")
                possible_names.add(base_name + ".mmproj-f16.gguf")
                possible_names.add(base_name + ".mmproj-F16.gguf")  # 大写 F16
        
        return list(possible_names)
    
    def list_all_mmproj_files(self, directory: str) -> List[str]:
        """
        列出目录中所有的 mmproj 文件
        
        Args:
            directory: 搜索目录
        
        Returns:
            mmproj 文件列表
        """
        mmproj_files = []
        
        if not os.path.exists(directory):
            return mmproj_files
        
        for root, _, files in os.walk(directory):
            for file in files:
                if 'mmproj' in file.lower() and file.endswith('.gguf'):
                    mmproj_files.append(os.path.join(root, file))
        
        return mmproj_files
    
    def suggest_mmproj_name(self, model_filename: str) -> str:
        """
        建议 mmproj 文件名
        
        Args:
            model_filename: 模型文件名
        
        Returns:
            建议的 mmproj 文件名
        """
        # 移除量化后缀
        base_name = re.sub(r'[-.]Q\d+_\d+\.gguf$', '', model_filename)
        return base_name + ".mmproj-f16.gguf"
