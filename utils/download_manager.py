# -*- coding: utf-8 -*-
"""
统一下载管理器
支持 GGUF 单文件和 Transformers 完整模型下载
"""

import os
import time
from pathlib import Path
from typing import Optional, List
from huggingface_hub import hf_hub_download, snapshot_download


class DownloadManager:
    """统一的模型下载管理器"""
    
    def __init__(self, max_retries: int = 3, max_workers: int = 4):
        """
        初始化下载管理器
        
        Args:
            max_retries: 最大重试次数
            max_workers: 并发下载线程数
        """
        self.max_retries = max_retries
        self.max_workers = max_workers
    
    def download_single_file(
        self,
        repo_id: str,
        filename: str,
        dest_dir: str,
        resume: bool = True
    ) -> Optional[str]:
        """
        下载单个文件（GGUF 模型）
        
        Args:
            repo_id: HuggingFace 仓库 ID
            filename: 文件名
            dest_dir: 目标目录
            resume: 是否支持断点续传
        
        Returns:
            下载文件的完整路径，失败返回 None
        """
        retry_count = 0
        
        while retry_count < self.max_retries:
            try:
                print(f"\n{'='*60}")
                if retry_count > 0:
                    print(f"🔄 Retry {retry_count}/{self.max_retries}")
                print(f"📥 Downloading: {filename}")
                print(f"📦 From: {repo_id}")
                print(f"📁 To: {dest_dir}")
                print(f"{'='*60}\n")
                
                # 确保目标目录存在
                os.makedirs(dest_dir, exist_ok=True)
                
                # 使用 hf_hub_download
                downloaded_path = hf_hub_download(
                    repo_id=repo_id,
                    filename=filename,
                    local_dir=dest_dir,
                    local_dir_use_symlinks=False,
                    resume_download=resume,
                )
                
                print(f"\n{'='*60}")
                print(f"✅ Downloaded: {filename}")
                print(f"{'='*60}\n")
                
                return downloaded_path
                
            except Exception as e:
                retry_count += 1
                if retry_count < self.max_retries:
                    wait_time = 5 * retry_count
                    print(f"\n⚠️ Download error: {e}")
                    print(f"⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    print(f"\n❌ Download failed after {self.max_retries} retries: {e}")
                    return None
    
    def download_repository(
        self,
        repo_id: str,
        local_dir: str,
        ignore_patterns: Optional[List[str]] = None,
        resume: bool = True
    ) -> bool:
        """
        下载完整仓库（Transformers 模型）
        
        Args:
            repo_id: HuggingFace 仓库 ID
            local_dir: 本地目录
            ignore_patterns: 忽略的文件模式
            resume: 是否支持断点续传
        
        Returns:
            成功返回 True，失败返回 False
        """
        if ignore_patterns is None:
            ignore_patterns = [
                "*.gguf",
                "GGUF/*",
                "*.bin",
                "*.msgpack",
            ]
        
        retry_count = 0
        
        while retry_count < self.max_retries:
            try:
                print(f"\n{'='*80}")
                if retry_count > 0:
                    print(f"🔄 Retry {retry_count}/{self.max_retries}")
                print(f"📥 [GGUF-VLM] Downloading Transformers Model")
                print(f"📦 Repository: {repo_id}")
                print(f"📁 Destination: {local_dir}")
                print(f"🚫 Excluding: {', '.join(ignore_patterns)}")
                print(f"⏳ Please wait, this may take several minutes...")
                print(f"{'='*80}\n")
                
                # 使用 tqdm_class=None 禁用内部进度条，我们自己显示状态
                snapshot_download(
                    repo_id=repo_id,
                    local_dir=local_dir,
                    local_dir_use_symlinks=False,
                    resume_download=resume,
                    max_workers=self.max_workers,
                    ignore_patterns=ignore_patterns,
                    tqdm_class=None,  # 禁用 tqdm 进度条
                )
                
                print(f"\n{'='*80}")
                print("✅ [GGUF-VLM] Model downloaded successfully!")
                print(f"📁 Location: {local_dir}")
                print(f"{'='*80}\n")
                
                return True
                
            except Exception as e:
                retry_count += 1
                if retry_count < self.max_retries:
                    wait_time = 5 * retry_count
                    print(f"\n⚠️ [GGUF-VLM] Download error: {e}")
                    print(f"⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    print(f"\n❌ [GGUF-VLM] Download failed after {self.max_retries} retries")
                    print(f"Error: {e}")
                    return False
    
    def check_repository_integrity(
        self,
        local_dir: str,
        required_files: Optional[List[str]] = None
    ) -> bool:
        """
        检查仓库完整性
        
        Args:
            local_dir: 本地目录
            required_files: 必需的文件列表
        
        Returns:
            完整返回 True，否则返回 False
        """
        if not os.path.exists(local_dir):
            return False
        
        if required_files is None:
            required_files = [
                "config.json",
                "model.safetensors.index.json",
            ]
        
        for file in required_files:
            file_path = os.path.join(local_dir, file)
            if not os.path.exists(file_path):
                print(f"⚠️ Missing required file: {file}")
                return False
        
        return True
    
    def check_disk_space(self, path: str, required_gb: float = 10.0) -> bool:
        """
        检查磁盘空间
        
        Args:
            path: 检查路径
            required_gb: 需要的空间（GB）
        
        Returns:
            空间足够返回 True，否则返回 False
        """
        try:
            import shutil
            stat = shutil.disk_usage(path)
            free_gb = stat.free / (1024**3)
            
            if free_gb < required_gb:
                print(f"⚠️ Low disk space: {free_gb:.2f} GB available, {required_gb:.2f} GB required")
                return False
            
            print(f"✓ Disk space OK: {free_gb:.2f} GB available")
            return True
            
        except Exception as e:
            print(f"⚠️ Could not check disk space: {e}")
            return True  # 继续执行


# 全局单例
_download_manager = None


def get_download_manager() -> DownloadManager:
    """获取全局下载管理器实例"""
    global _download_manager
    if _download_manager is None:
        _download_manager = DownloadManager()
    return _download_manager
