"""
Cache Manager - 管理模型缓存和签名验证
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class CacheManager:
    """模型缓存管理器"""
    
    def __init__(self):
        self._cache: Dict = {}
        self._cache_signature: Optional[Tuple] = None
    
    def compute_signature(self, search_paths: List[str], config_paths: List[Path]) -> Tuple:
        """
        生成缓存签名，用于检测文件系统变化
        
        Args:
            search_paths: 模型搜索路径列表
            config_paths: 配置文件路径列表
        
        Returns:
            签名元组
        """
        file_entries = []
        
        # 扫描所有 GGUF 文件
        for base in search_paths:
            if not os.path.exists(base):
                file_entries.append((base, "__missing__", 0, 0))
                continue
            
            for root, _, files in os.walk(base):
                for file in files:
                    if file.lower().endswith(".gguf"):
                        full_path = os.path.join(root, file)
                        try:
                            stat_result = os.stat(full_path)
                            size = stat_result.st_size
                            mtime = int(stat_result.st_mtime)
                        except OSError:
                            size = 0
                            mtime = 0
                        
                        rel_path = os.path.relpath(full_path, base)
                        file_entries.append((base, rel_path, size, mtime))
        
        file_entries.sort()
        
        # 配置文件签名
        config_sigs = []
        for config_path in config_paths:
            try:
                stat = config_path.stat()
                config_sigs.append((str(config_path), int(stat.st_mtime), stat.st_size))
            except FileNotFoundError:
                config_sigs.append((str(config_path), "missing", 0))
            except OSError:
                config_sigs.append((str(config_path), "error", 0))
        
        return (
            tuple(file_entries),
            tuple(sorted(search_paths)),
            tuple(config_sigs)
        )
    
    def is_cache_valid(self, current_signature: Tuple) -> bool:
        """
        检查缓存是否有效
        
        Args:
            current_signature: 当前签名
        
        Returns:
            缓存是否有效
        """
        if self._cache_signature is None:
            return False
        
        return self._cache_signature == current_signature
    
    def get(self, key: str, default=None):
        """获取缓存值"""
        return self._cache.get(key, default)
    
    def set(self, key: str, value):
        """设置缓存值"""
        self._cache[key] = value
    
    def update_signature(self, signature: Tuple):
        """更新缓存签名"""
        self._cache_signature = signature
    
    def clear(self, reason: str = None):
        """
        清除缓存
        
        Args:
            reason: 清除原因（用于日志）
        """
        if reason:
            print(f"🔄 Clearing cache: {reason}")
        else:
            print("🔄 Clearing cache")
        
        self._cache.clear()
        self._cache_signature = None
    
    def has_key(self, key: str) -> bool:
        """检查缓存中是否存在指定键"""
        return key in self._cache
