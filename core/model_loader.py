"""
Model Loader - 负责加载和管理 GGUF 模型
增强版：集成智能 mmproj 查找
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import folder_paths

# 导入 mmproj 查找器 - 使用相对导入
try:
    from ..utils.mmproj_finder import MMProjFinder
except (ImportError, ValueError):
    # 备用方案
    try:
        from utils.mmproj_finder import MMProjFinder
    except ImportError:
        MMProjFinder = None


class ModelLoader:
    """GGUF 模型加载器"""
    
    def __init__(self, model_dirs: List[str] = None):
        """
        初始化模型加载器
        
        Args:
            model_dirs: 模型目录列表，如果为 None 则使用默认目录
        """
        if model_dirs is None:
            self.model_dirs = self._get_default_model_dirs()
        else:
            self.model_dirs = model_dirs
        
        # 初始化 mmproj 查找器
        if MMProjFinder:
            self.mmproj_finder = MMProjFinder(self.model_dirs)
        else:
            self.mmproj_finder = None
    
    def _get_default_model_dirs(self) -> List[str]:
        """获取默认模型目录"""
        dirs = []
        
        # LLM/GGUF 目录（主要目录）
        llm_gguf_dir = os.path.join(folder_paths.models_dir, "LLM", "GGUF")
        os.makedirs(llm_gguf_dir, exist_ok=True)
        dirs.append(llm_gguf_dir)
        
        # ComfyUI text_encoders 目录（兼容）
        text_encoders_dir = os.path.join(folder_paths.models_dir, "text_encoders")
        if os.path.exists(text_encoders_dir):
            dirs.append(text_encoders_dir)
        
        # ComfyUI clip 目录
        clip_dir = os.path.join(folder_paths.models_dir, "clip")
        if os.path.exists(clip_dir):
            dirs.append(clip_dir)
        
        # ComfyUI clip/gguf 子目录
        clip_gguf_dir = os.path.join(folder_paths.models_dir, "clip", "gguf")
        if os.path.exists(clip_gguf_dir):
            dirs.append(clip_gguf_dir)
        
        # 兼容旧版 VLM_GGUF 目录
        vlm_gguf_dir = os.path.join(folder_paths.models_dir, "VLM_GGUF")
        if os.path.exists(vlm_gguf_dir):
            dirs.append(vlm_gguf_dir)
        
        # 从 folder_paths 获取额外配置的目录
        try:
            configured = folder_paths.get_folder_paths("text_encoders")
            if configured:
                dirs.extend(configured)
        except Exception as e:
            print(f"⚠️  Could not get folder_paths for text_encoders: {e}")
        
        try:
            configured_clip = folder_paths.get_folder_paths("clip")
            if configured_clip:
                dirs.extend(configured_clip)
        except Exception as e:
            print(f"⚠️  Could not get folder_paths for clip: {e}")
        
        # 去重
        unique_dirs = []
        seen = set()
        for path in dirs:
            if path not in seen:
                unique_dirs.append(path)
                seen.add(path)
        
        return unique_dirs
    
    def scan_models(self, log_paths: bool = False) -> Dict[str, str]:
        """
        扫描所有模型目录，查找 GGUF 文件
        
        Args:
            log_paths: 是否打印扫描路径
        
        Returns:
            {filename: full_path} 字典
        """
        models = {}
        
        for base_dir in self.model_dirs:
            if not os.path.exists(base_dir):
                continue
            
            for root, _, files in os.walk(base_dir):
                for file in files:
                    if file.lower().endswith(".gguf"):
                        full_path = os.path.join(root, file)
                        
                        # 如果文件名已存在，保留第一个找到的
                        if file not in models:
                            models[file] = full_path
        
        return models
    
    def find_model(self, filename: str) -> Optional[str]:
        """
        查找指定的模型文件
        
        Args:
            filename: 模型文件名
        
        Returns:
            模型完整路径，未找到返回 None
        """
        models = self.scan_models()
        return models.get(filename)
    
    def find_mmproj(self, model_filename: str, mmproj_name: str = None) -> Optional[str]:
        """
        查找模型对应的 mmproj 文件（增强版）
        
        Args:
            model_filename: 模型文件名
            mmproj_name: mmproj 文件名（可选，如果不提供则自动查找）
        
        Returns:
            mmproj 完整路径，未找到返回 None
        """
        # 如果指定了 mmproj 文件名，直接查找
        if mmproj_name:
            # 首先在模型所在目录查找
            model_path = self.find_model(model_filename)
            if model_path:
                model_dir = os.path.dirname(model_path)
                mmproj_path = os.path.join(model_dir, mmproj_name)
                if os.path.exists(mmproj_path):
                    return mmproj_path
            
            # 在所有模型目录中查找
            for base_dir in self.model_dirs:
                if not os.path.exists(base_dir):
                    continue
                
                for root, _, files in os.walk(base_dir):
                    if mmproj_name in files:
                        return os.path.join(root, mmproj_name)
            
            return None
        
        # 自动查找 mmproj 文件
        model_path = self.find_model(model_filename)
        if not model_path:
            return None
        
        model_dir = os.path.dirname(model_path)
        
        # 使用智能查找器（如果可用）
        if self.mmproj_finder:
            mmproj_path = self.mmproj_finder.find_mmproj(model_filename, model_dir)
            
            if mmproj_path:
                return mmproj_path
            
            # 如果没找到，列出可用的 mmproj 文件供参考
            available_mmproj = self.mmproj_finder.list_all_mmproj_files(model_dir)
            if available_mmproj:
                print(f"📁 Available mmproj files in {model_dir}:")
                for mmproj in available_mmproj:
                    print(f"   - {os.path.basename(mmproj)}")
                
                # 建议文件名
                suggested_name = self.mmproj_finder.suggest_mmproj_name(model_filename)
                print(f"💡 Suggested mmproj filename: {suggested_name}")
        
        return None
    
    def get_model_info(self, filename: str) -> Optional[Dict]:
        """
        获取模型文件信息
        
        Args:
            filename: 模型文件名
        
        Returns:
            模型信息字典
        """
        model_path = self.find_model(filename)
        if not model_path:
            return None
        
        try:
            stat = os.stat(model_path)
            return {
                'filename': filename,
                'path': model_path,
                'size': stat.st_size,
                'mtime': stat.st_mtime,
                'exists': True
            }
        except OSError:
            return None
    
    def list_models(self, pattern: str = None) -> List[str]:
        """
        列出所有模型文件名
        
        Args:
            pattern: 可选的过滤模式（不区分大小写）
        
        Returns:
            模型文件名列表
        """
        models = self.scan_models()
        filenames = list(models.keys())
        
        if pattern:
            pattern_lower = pattern.lower()
            filenames = [f for f in filenames if pattern_lower in f.lower()]
        
        return sorted(filenames)
