"""
File Downloader - 负责从 HuggingFace 下载模型文件
"""

import os
import requests
from pathlib import Path
from typing import Optional, Callable
from tqdm import tqdm


class FileDownloader:
    """文件下载器"""
    
    def __init__(self):
        """初始化下载器"""
        self.session = requests.Session()
    
    def download_file(
        self,
        url: str,
        dest_path: str,
        desc: str = None,
        progress_callback: Callable = None,
        chunk_size: int = 8192
    ) -> Optional[str]:
        """
        下载文件
        
        Args:
            url: 下载 URL
            dest_path: 目标路径
            desc: 进度条描述
            progress_callback: 进度回调函数
            chunk_size: 下载块大小
        
        Returns:
            下载后的文件路径，失败返回 None
        """
        try:
            # 创建目标目录
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            
            # 发起请求
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 获取文件大小
            total_size = int(response.headers.get('content-length', 0))
            
            # 下载文件
            desc = desc or os.path.basename(dest_path)
            
            with open(dest_path, 'wb') as f:
                with tqdm(
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    desc=desc
                ) as pbar:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
                            
                            if progress_callback:
                                progress_callback(len(chunk), total_size)
            
            print(f"✅ Downloaded: {dest_path}")
            return dest_path
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Download failed: {e}")
            # 清理部分下载的文件
            if os.path.exists(dest_path):
                os.remove(dest_path)
            return None
        
        except Exception as e:
            print(f"❌ Unexpected error during download: {e}")
            if os.path.exists(dest_path):
                os.remove(dest_path)
            return None
    
    def download_from_huggingface(
        self,
        repo_id: str,
        filename: str,
        dest_dir: str,
        desc: str = None
    ) -> Optional[str]:
        """
        从 HuggingFace 下载文件（使用统一的下载管理器）
        
        Args:
            repo_id: HuggingFace 仓库 ID (例如: "Qwen/Qwen2.5-7B-Instruct-GGUF")
            filename: 文件名
            dest_dir: 目标目录
            desc: 进度条描述（已弃用，保留用于兼容性）
        
        Returns:
            下载后的文件路径，失败返回 None
        """
        dest_path = os.path.join(dest_dir, filename)
        
        # 检查文件是否已存在
        if os.path.exists(dest_path):
            print(f"✅ File already exists: {dest_path}")
            return dest_path
        
        # 使用统一的下载管理器
        from .download_manager import get_download_manager
        
        download_manager = get_download_manager()
        downloaded_path = download_manager.download_single_file(
            repo_id=repo_id,
            filename=filename,
            dest_dir=dest_dir,
            resume=True
        )
        
        return downloaded_path
    
    def get_remote_file_size(self, url: str) -> Optional[int]:
        """
        获取远程文件大小
        
        Args:
            url: 文件 URL
        
        Returns:
            文件大小（字节），失败返回 None
        """
        try:
            response = self.session.head(url, timeout=10)
            response.raise_for_status()
            return int(response.headers.get('content-length', 0))
        except Exception as e:
            print(f"⚠️  Failed to get file size: {e}")
            return None
    
    def verify_file_integrity(self, file_path: str, expected_size: int = None) -> bool:
        """
        验证文件完整性
        
        Args:
            file_path: 文件路径
            expected_size: 期望的文件大小（字节）
        
        Returns:
            文件是否完整
        """
        if not os.path.exists(file_path):
            return False
        
        if expected_size is not None:
            actual_size = os.path.getsize(file_path)
            if actual_size != expected_size:
                print(f"⚠️  File size mismatch: expected {expected_size}, got {actual_size}")
                return False
        
        return True
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """
        格式化文件大小
        
        Args:
            size_bytes: 字节数
        
        Returns:
            格式化的大小字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
