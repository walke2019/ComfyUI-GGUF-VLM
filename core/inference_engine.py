"""
Inference Engine - 负责模型推理和生成
"""

from typing import Dict, List, Optional, Any
import os
import numpy as np


class InferenceEngine:
    """GGUF 模型推理引擎"""
    
    def __init__(self):
        """初始化推理引擎"""
        self.loaded_models: Dict[str, Any] = {}
        self.model_contexts: Dict[str, Any] = {}

    @staticmethod
    def create_vision_chat_handler(model_path: str, mmproj_path: str, verbose: bool = False):
        """Create the best llama-cpp-python vision chat handler available."""
        from llama_cpp import llama_chat_format

        model_name = os.path.basename(model_path).lower()
        handler_names = []

        if "qwen3" in model_name and "vl" in model_name:
            handler_names.extend(["Qwen3VLChatHandler", "Qwen25VLChatHandler"])
        elif "qwen2.5" in model_name and "vl" in model_name:
            handler_names.append("Qwen25VLChatHandler")
        elif "qwen2" in model_name and "vl" in model_name:
            handler_names.extend(["Qwen25VLChatHandler", "Llava15ChatHandler"])
        elif "gemma" in model_name:
            handler_names.extend(["Gemma3ChatHandler", "Llava15ChatHandler"])

        handler_names.append("Llava15ChatHandler")

        seen = set()
        for handler_name in handler_names:
            if handler_name in seen:
                continue
            seen.add(handler_name)
            handler_cls = getattr(llama_chat_format, handler_name, None)
            if handler_cls:
                print(f"🧩 Using llama.cpp vision handler: {handler_name}")
                return handler_cls(clip_model_path=mmproj_path, verbose=verbose)

        raise ImportError("No supported llama-cpp-python vision chat handler found")
    
    def load_model(self, model_path: str, **kwargs) -> bool:
        """
        加载模型到内存
        
        Args:
            model_path: 模型文件路径
            **kwargs: 额外的加载参数
        
        Returns:
            是否加载成功
        """
        try:
            from llama_cpp import Llama
            from llama_cpp.llama_chat_format import Llava15ChatHandler
            
            # 检查是否已加载
            if model_path in self.loaded_models:
                print(f"ℹ️ Model already loaded: {model_path}")
                return True
            
            # 验证模型文件存在
            import os
            if not os.path.exists(model_path):
                print(f"❌ Model file not found: {model_path}")
                return False
            
            # 检查文件大小
            file_size = os.path.getsize(model_path) / (1024**3)  # GB
            print(f"📊 Model file size: {file_size:.2f} GB")
            
            # 加载模型
            n_ctx = kwargs.get('n_ctx', 8192)
            n_gpu_layers = kwargs.get('n_gpu_layers', -1)
            verbose = kwargs.get('verbose', False)
            
            # 检查是否是视觉模型
            mmproj_path = kwargs.get('mmproj_path')
            
            print(f"🔧 Loading parameters:")
            print(f"   - n_ctx: {n_ctx}")
            print(f"   - n_gpu_layers: {n_gpu_layers}")
            print(f"   - verbose: {verbose}")
            
            if mmproj_path:
                # 验证mmproj文件存在
                if not os.path.exists(mmproj_path):
                    print(f"❌ mmproj file not found: {mmproj_path}")
                    return False
                
                mmproj_size = os.path.getsize(mmproj_path) / (1024**2)  # MB
                print(f"   - mmproj: {mmproj_path} ({mmproj_size:.2f} MB)")
                
                # 视觉语言模型
                print("🔄 Loading vision model with mmproj...")
                chat_handler = self.create_vision_chat_handler(model_path, mmproj_path, verbose=verbose)
                llm = Llama(
                    model_path=model_path,
                    chat_handler=chat_handler,
                    n_ctx=n_ctx,
                    n_gpu_layers=n_gpu_layers,
                    verbose=verbose,
                    logits_all=True
                )
            else:
                # 纯文本模型
                print("🔄 Loading text model...")
                llm = Llama(
                    model_path=model_path,
                    n_ctx=n_ctx,
                    n_gpu_layers=n_gpu_layers,
                    verbose=verbose
                )
            
            self.loaded_models[model_path] = llm
            print(f"✅ Model loaded successfully: {os.path.basename(model_path)}")
            return True
            
        except FileNotFoundError as e:
            print(f"❌ File not found error: {e}")
            print(f"   Model path: {model_path}")
            if mmproj_path:
                print(f"   mmproj path: {mmproj_path}")
            return False
        except ImportError as e:
            print(f"❌ Import error: {e}")
            print("   Make sure llama-cpp-python is installed correctly")
            return False
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            print(f"   Model path: {model_path}")
            import traceback
            print(f"   Traceback:\n{traceback.format_exc()}")
            return False
    
    def unload_model(self, model_path: str):
        """
        卸载模型
        
        Args:
            model_path: 模型文件路径
        """
        if model_path in self.loaded_models:
            del self.loaded_models[model_path]
            if model_path in self.model_contexts:
                del self.model_contexts[model_path]
    
    def generate_text(
        self,
        model_path: str,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs
    ) -> str:
        """
        生成文本
        
        Args:
            model_path: 模型路径
            prompt: 输入提示
            max_tokens: 最大生成 token 数
            temperature: 温度参数
            top_p: Top-p 采样参数
            **kwargs: 其他生成参数
        
        Returns:
            生成的文本
        """
        if model_path not in self.loaded_models:
            raise ValueError(f"Model not loaded: {model_path}")
        
        llm = self.loaded_models[model_path]
        
        try:
            output = llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                echo=False,
                **kwargs
            )
            
            return output['choices'][0]['text']
        
        except Exception as e:
            print(f"❌ Generation failed: {e}")
            return f"Error: {str(e)}"
    
    def generate_with_image(
        self,
        model_path: str,
        image_data: Any,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        使用图像生成文本（视觉语言模型）
        
        Args:
            model_path: 模型路径
            image_data: 图像数据
            prompt: 文本提示
            max_tokens: 最大生成 token 数
            temperature: 温度参数
            **kwargs: 其他参数
        
        Returns:
            生成的文本
        """
        if model_path not in self.loaded_models:
            raise ValueError(f"Model not loaded: {model_path}")
        
        llm = self.loaded_models[model_path]
        
        try:
            # 构建消息格式
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_data}},
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
            
            output = llm.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            return output['choices'][0]['message']['content']
        
        except Exception as e:
            print(f"❌ Vision generation failed: {e}")
            return f"Error: {str(e)}"
    
    def is_model_loaded(self, model_path: str) -> bool:
        """检查模型是否已加载"""
        return model_path in self.loaded_models
    
    def get_loaded_models(self) -> List[str]:
        """获取所有已加载的模型路径"""
        return list(self.loaded_models.keys())
    
    def clear_all(self):
        """清除所有已加载的模型"""
        # 显式删除模型对象以释放内存
        for model_path in list(self.loaded_models.keys()):
            try:
                del self.loaded_models[model_path]
            except:
                pass
        
        self.loaded_models.clear()
        self.model_contexts.clear()
        
        # 强制垃圾回收
        import gc
        gc.collect()
        
        # 如果使用CUDA，清理GPU缓存
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                print("✅ GPU cache cleared")
        except ImportError:
            pass


_GLOBAL_INFERENCE_ENGINE: Optional[InferenceEngine] = None


def get_global_inference_engine() -> InferenceEngine:
    """Return the shared GGUF inference engine used by all nodes.

    Memory cleanup nodes must operate on the same engine instance that text and
    vision nodes use; otherwise loaded llama.cpp models remain resident.
    """
    global _GLOBAL_INFERENCE_ENGINE
    if _GLOBAL_INFERENCE_ENGINE is None:
        _GLOBAL_INFERENCE_ENGINE = InferenceEngine()
    return _GLOBAL_INFERENCE_ENGINE
