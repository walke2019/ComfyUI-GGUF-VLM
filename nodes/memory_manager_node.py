"""
Memory Manager Node - 显存/内存管理节点
用于手动释放模型占用的显存和内存
"""

import gc
import sys
from pathlib import Path

# 添加父目录到路径
module_path = Path(__file__).parent.parent
if str(module_path) not in sys.path:
    sys.path.insert(0, str(module_path))

try:
    from core.inference_engine import InferenceEngine
except ImportError as e:
    print(f"[ComfyUI-GGUF-VLM] Import error in memory_manager_node: {e}")
    from ..core.inference_engine import InferenceEngine


class MemoryManagerNode:
    """显存/内存管理节点"""
    
    # 全局推理引擎引用
    _inference_engine = None
    
    @classmethod
    def _get_engine(cls):
        """获取推理引擎"""
        if cls._inference_engine is None:
            cls._inference_engine = InferenceEngine()
        return cls._inference_engine
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "action": (["Clear All Models", "Force GC", "Clear GPU Cache", "Full Cleanup"], {
                    "default": "Full Cleanup",
                    "tooltip": "选择清理操作"
                }),
            },
            "optional": {
                "trigger": ("*", {
                    "tooltip": "连接任意输出以触发清理（可选）"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status",)
    FUNCTION = "manage_memory"
    CATEGORY = "🤖 GGUF-VLM/⚙️ Utils"
    OUTPUT_NODE = True
    
    def manage_memory(self, action, trigger=None):
        """执行内存管理操作"""
        try:
            status_messages = []
            
            if action == "Clear All Models" or action == "Full Cleanup":
                # 清除所有已加载的模型
                engine = self._get_engine()
                loaded_models = engine.get_loaded_models()
                
                if loaded_models:
                    status_messages.append(f"🗑️ Unloading {len(loaded_models)} model(s)...")
                    for model_path in loaded_models:
                        status_messages.append(f"   - {model_path}")
                    
                    engine.clear_all()
                    status_messages.append("✅ All models unloaded")
                else:
                    status_messages.append("ℹ️ No models currently loaded")
            
            if action == "Force GC" or action == "Full Cleanup":
                # 强制垃圾回收
                collected = gc.collect()
                status_messages.append(f"🧹 Garbage collection: {collected} objects collected")
            
            if action == "Clear GPU Cache" or action == "Full Cleanup":
                # 清理GPU缓存
                try:
                    import torch
                    if torch.cuda.is_available():
                        # 获取清理前的显存使用情况
                        before_allocated = torch.cuda.memory_allocated() / 1024**3
                        before_reserved = torch.cuda.memory_reserved() / 1024**3
                        
                        torch.cuda.empty_cache()
                        torch.cuda.synchronize()
                        
                        # 获取清理后的显存使用情况
                        after_allocated = torch.cuda.memory_allocated() / 1024**3
                        after_reserved = torch.cuda.memory_reserved() / 1024**3
                        
                        freed_allocated = before_allocated - after_allocated
                        freed_reserved = before_reserved - after_reserved
                        
                        status_messages.append("🎮 GPU cache cleared")
                        status_messages.append(f"   Allocated: {before_allocated:.2f}GB → {after_allocated:.2f}GB (freed: {freed_allocated:.2f}GB)")
                        status_messages.append(f"   Reserved: {before_reserved:.2f}GB → {after_reserved:.2f}GB (freed: {freed_reserved:.2f}GB)")
                    else:
                        status_messages.append("ℹ️ CUDA not available, skipping GPU cache clear")
                except ImportError:
                    status_messages.append("⚠️ PyTorch not available, cannot clear GPU cache")
                except Exception as e:
                    status_messages.append(f"⚠️ Error clearing GPU cache: {e}")
            
            # 组合所有状态消息
            status = "\n".join(status_messages)
            print(f"\n{'='*60}")
            print("🧹 Memory Manager")
            print(f"{'='*60}")
            print(status)
            print(f"{'='*60}\n")
            
            return (status,)
        
        except Exception as e:
            import traceback
            error_msg = f"❌ Memory management error: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            return (error_msg,)


# 节点注册
NODE_CLASS_MAPPINGS = {
    "MemoryManagerNode": MemoryManagerNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MemoryManagerNode": "🧹 Memory Manager (GGUF)",
}
