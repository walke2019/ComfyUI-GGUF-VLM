# -*- coding: utf-8 -*-
"""
项目清理脚本
删除冗余、作废、无用的代码和文件
"""

import os
import shutil
from pathlib import Path

def cleanup_project():
    """清理项目"""
    print("\n" + "="*80)
    print("🧹 开始清理项目")
    print("="*80 + "\n")
    
    project_root = Path(__file__).parent
    
    # 要删除的测试文件和临时文件
    files_to_remove = [
        "Test/test_node_categories.py",
        "Test/test_categories_simple.py",
        "Test/test_text_loader_models.py",
        "Test/test_registry_models.py",
        "Test/test_yaml_config.py",
        "Test/test_transformers_path.py",
        "Test/README_模型下载说明.md",
        "check_all_nodes.py",  # 已完成任务，可以删除
    ]
    
    removed_count = 0
    
    for file_path in files_to_remove:
        full_path = project_root / file_path
        if full_path.exists():
            try:
                full_path.unlink()
                print(f"✓ 删除: {file_path}")
                removed_count += 1
            except Exception as e:
                print(f"✗ 无法删除 {file_path}: {e}")
    
    # 保留的有用测试文件
    useful_tests = [
        "Test/debug_node_models.py",
        "Test/check_download_progress.py",
    ]
    
    print(f"\n📝 保留的测试文件:")
    for test_file in useful_tests:
        full_path = project_root / test_file
        if full_path.exists():
            print(f"  ✓ {test_file}")
    
    print(f"\n{'='*80}")
    print(f"✅ 清理完成！删除了 {removed_count} 个文件")
    print(f"{'='*80}\n")
    
    # 显示项目结构
    print("📁 当前项目结构:\n")
    
    important_dirs = [
        "nodes/",
        "core/",
        "utils/",
        "config/",
        "Test/",
    ]
    
    for dir_name in important_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"📂 {dir_name}")
            for file in sorted(dir_path.glob("*.py")):
                if file.name != "__init__.py":
                    size_kb = file.stat().st_size / 1024
                    print(f"   📄 {file.name:40s} {size_kb:>6.1f} KB")
            print()

if __name__ == "__main__":
    cleanup_project()
