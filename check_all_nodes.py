"""
检查所有节点是否能正确加载
"""

import sys
from pathlib import Path

# 添加模块路径
module_path = Path(__file__).parent
sys.path.insert(0, str(module_path))

def check_all_nodes():
    """检查所有节点"""
    print("="*80)
    print("检查所有节点文件")
    print("="*80)
    
    nodes_to_check = {
        "Legacy Nodes": "nodes/__init__.py",
        "Vision Nodes (GGUF)": "nodes/vision_node.py",
        "Vision Nodes (Transformers)": "nodes/vision_node_transformers.py",
        "Multi-Image Analysis": "nodes/multi_image_node.py",
        "System Prompt Config": "nodes/system_prompt_node.py",
        "Nexa SDK Nodes": "nodes/nexa_text_node.py",
        "Text Generation Nodes (New)": "nodes/text_generation_nodes.py",
        "Model Manager": "custom_model_manager.py",
    }
    
    print("\n📁 检查节点文件:")
    all_exist = True
    for name, path in nodes_to_check.items():
        file_path = Path(__file__).parent / path
        if file_path.exists():
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name} - 文件不存在: {path}")
            all_exist = False
    
    if not all_exist:
        print("\n❌ 部分节点文件缺失！")
        return False
    
    print("\n✅ 所有节点文件都存在")
    
    # 检查节点类定义
    print("\n🔍 检查节点类定义:")
    
    expected_classes = {
        "nodes/vision_node.py": ["VisionLanguageNode", "VisionModelLoader"],
        "nodes/vision_node_transformers.py": ["VisionLanguageNodeTransformers", "VisionModelLoaderTransformers"],
        "nodes/multi_image_node.py": ["MultiImageAnalysis", "MultiImageLoader"],
        "nodes/system_prompt_node.py": ["SystemPromptConfig"],
        "nodes/nexa_text_node.py": ["NexaTextGeneration"],
        "nodes/text_generation_nodes.py": ["LocalTextModelLoader", "RemoteTextModelSelector", "TextGeneration"],
    }
    
    import ast
    
    for file_path, expected in expected_classes.items():
        full_path = Path(__file__).parent / file_path
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content)
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            
            missing = [cls for cls in expected if cls not in classes]
            if missing:
                print(f"  ⚠️  {file_path}: 缺少类 {missing}")
            else:
                print(f"  ✅ {file_path}: {len(expected)} 个类")
        except Exception as e:
            print(f"  ❌ {file_path}: 解析失败 - {e}")
    
    print("\n" + "="*80)
    print("✅ 节点检查完成")
    print("="*80)
    print("\n💡 下一步:")
    print("  1. 重启 ComfyUI")
    print("  2. 查看控制台输出，确认所有节点加载成功")
    print("  3. 检查节点菜单中是否有以下分类:")
    print("     - 🤖 GGUF-VLM/Text")
    print("     - 🖼️ GGUF-VLM/Vision")
    print("     - 🎨 GGUF-VLM/Multi-Image")
    print()
    
    return True

if __name__ == "__main__":
    success = check_all_nodes()
    sys.exit(0 if success else 1)
