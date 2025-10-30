"""
Vision Node (Transformers Mode) - Transformers 模式的视觉语言模型节点
支持 Qwen3-VL 等完整的 Transformers 模型（使用最新 API）
"""

import os
import sys
import torch
from pathlib import Path
from PIL import Image
from torchvision.transforms import ToPILImage
import folder_paths

# 添加父目录到路径
module_path = Path(__file__).parent.parent
if str(module_path) not in sys.path:
    sys.path.insert(0, str(module_path))

try:
    from core.inference.transformers_engine import TransformersInferenceEngine
    from utils.system_prompts import SystemPromptsManager
    from config.node_definitions import (
        SEED_INPUT,
        TEMPERATURE_INPUT,
        TOP_P_INPUT,
        TOP_K_INPUT,
        REPETITION_PENALTY_INPUT,
        PROMPT_INPUT,
        SYSTEM_PROMPT_INPUT,
        TRANSFORMERS_QUANTIZATION_INPUT,
        TRANSFORMERS_ATTENTION_INPUT,
        TRANSFORMERS_PIXELS_INPUT,
        KEEP_MODEL_LOADED_INPUT,
        TEXT_OUTPUT,
        TRANSFORMERS_MODEL_OUTPUT,
        merge_inputs
    )
except ImportError:
    from ..core.inference.transformers_engine import TransformersInferenceEngine
    from ..utils.system_prompts import SystemPromptsManager
    from ..config.node_definitions import (
        SEED_INPUT,
        TEMPERATURE_INPUT,
        TOP_P_INPUT,
        TOP_K_INPUT,
        REPETITION_PENALTY_INPUT,
        PROMPT_INPUT,
        SYSTEM_PROMPT_INPUT,
        TRANSFORMERS_QUANTIZATION_INPUT,
        TRANSFORMERS_ATTENTION_INPUT,
        TRANSFORMERS_PIXELS_INPUT,
        KEEP_MODEL_LOADED_INPUT,
        TEXT_OUTPUT,
        TRANSFORMERS_MODEL_OUTPUT,
        merge_inputs
    )


class VisionModelLoaderTransformers:
    """Transformers 模式的视觉模型加载器"""
    
    # 全局引擎实例
    _engine = None
    
    @classmethod
    def _get_engine(cls):
        """获取全局引擎实例"""
        if cls._engine is None:
            cls._engine = TransformersInferenceEngine()
        return cls._engine
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": merge_inputs(
                {
                    "model": (
                        [
                            "Huihui-Qwen3-VL-4B-Instruct-abliterated",
                            "Huihui-Qwen3-VL-8B-Instruct-abliterated",
                            "Qwen3-VL-4B-Instruct-FP8",
                            "Qwen3-VL-4B-Thinking-FP8",
                            "Qwen3-VL-8B-Instruct-FP8",
                            "Qwen3-VL-8B-Thinking-FP8",
                            "Qwen3-VL-4B-Instruct",
                            "Qwen3-VL-4B-Thinking",
                            "Qwen3-VL-8B-Instruct",
                            "Qwen3-VL-8B-Thinking"
                        ],
                        {
                            "default": "Huihui-Qwen3-VL-4B-Instruct-abliterated",
                            "tooltip": "选择 Qwen3-VL 模型"
                        }
                    ),
                },
                TRANSFORMERS_QUANTIZATION_INPUT,
                TRANSFORMERS_ATTENTION_INPUT,
                KEEP_MODEL_LOADED_INPUT,
                TRANSFORMERS_PIXELS_INPUT
            )
        }
    
    RETURN_TYPES = TRANSFORMERS_MODEL_OUTPUT["types"]
    RETURN_NAMES = TRANSFORMERS_MODEL_OUTPUT["names"]
    FUNCTION = "load_model"
    CATEGORY = "🤖 GGUF-Fusion/Transformers"
    
    def load_model(
        self,
        model,
        quantization,
        attention,
        keep_model_loaded,
        min_pixels,
        max_pixels
    ):
        """加载 Transformers 模型"""
        
        # 确定模型 ID
        if model == "Huihui-Qwen3-VL-8B-Instruct-abliterated":
            model_id = "huihui-ai/Huihui-Qwen3-VL-8B-Instruct-abliterated"
        else:
            model_id = f"qwen/{model}"
        
        # 构建配置
        config = {
            "model_name": model,
            "model_id": model_id,
            "quantization": quantization,
            "attention": attention,
            "min_pixels": min_pixels,
            "max_pixels": max_pixels,
            "keep_loaded": keep_model_loaded,
        }
        
        # 加载模型
        engine = self._get_engine()
        success = engine.load_model(config)
        
        if not success:
            raise RuntimeError(f"Failed to load model: {model}")
        
        print(f"✅ Transformers model loaded: {model}")
        
        return (config,)


class VisionLanguageNodeTransformers:
    """Transformers 模式的视觉语言节点（Qwen3-VL 优化）"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": merge_inputs(
                {
                    "model_config": ("TRANSFORMERS_MODEL",),
                },
                PROMPT_INPUT,
                TEMPERATURE_INPUT,
                TOP_P_INPUT,
                TOP_K_INPUT,
                REPETITION_PENALTY_INPUT,
                {
                    "max_tokens": (
                        "INT",
                        {
                            "default": 2048,
                            "min": 128,
                            "max": 256000,
                            "step": 1,
                            "tooltip": "最大生成 token 数（Qwen3-VL 推荐: 16384）"
                        }
                    ),
                },
                SEED_INPUT
            ),
            "optional": merge_inputs(
                {
                    "image": ("IMAGE",),
                },
                SYSTEM_PROMPT_INPUT
            )
        }
    
    RETURN_TYPES = TEXT_OUTPUT["types"]
    RETURN_NAMES = TEXT_OUTPUT["names"]
    FUNCTION = "generate"
    CATEGORY = "🤖 GGUF-Fusion/Transformers"
    OUTPUT_NODE = True
    
    def generate(
        self,
        model_config,
        prompt,
        temperature,
        top_p,
        top_k,
        repetition_penalty,
        max_tokens,
        seed,
        image=None,
        system_prompt=""
    ):
        """生成文本（使用 Qwen3-VL 新 API）"""
        
        engine = VisionModelLoaderTransformers._get_engine()
        
        # 确保模型已加载
        if engine.model is None or engine.processor is None:
            print("⚠️  Model not loaded, loading now...")
            success = engine.load_model(model_config)
            if not success:
                raise RuntimeError(f"Failed to load model: {model_config.get('model_name', 'unknown')}")
        
        # 准备图像
        temp_path = None
        if image is not None:
            pil_image = ToPILImage()(image[0].permute(2, 0, 1))
            temp_path = Path(folder_paths.temp_directory) / f"temp_image_{seed}.png"
            pil_image.save(temp_path)
        
        # 构建消息（Qwen3-VL 格式）
        messages = []
        
        # 构建用户消息内容
        user_content = []
        
        if temp_path:
            user_content.append({
                "type": "image",
                "image": str(temp_path)
            })
        
        # 将系统提示词合并到用户文本中
        if system_prompt and system_prompt.strip():
            final_text = f"{system_prompt.strip()}\n\n{prompt}"
        else:
            # 使用默认系统提示词
            default_prompt = SystemPromptsManager.get_preset("default")
            final_text = f"{default_prompt}\n\n{prompt}"
        
        user_content.append({
            "type": "text",
            "text": final_text
        })
        
        messages.append({
            "role": "user",
            "content": user_content
        })
        
        # 执行推理（使用 Qwen3-VL 推荐参数）
        try:
            result = engine.inference(
                messages=messages,
                temperature=temperature,
                max_new_tokens=max_tokens,
                seed=seed,
                top_p=top_p,
                top_k=top_k,
                repetition_penalty=repetition_penalty
            )
            
            print(f"✅ Generated text ({len(result)} chars)")
            
            # 清理临时文件
            if temp_path and temp_path.exists():
                temp_path.unlink()
            
            # 如果不保持加载，卸载模型
            if not model_config.get("keep_loaded", False):
                engine.unload()
            
            return (result,)
            
        except Exception as e:
            print(f"❌ Generation failed: {e}")
            import traceback
            traceback.print_exc()
            raise


# 导出节点
NODE_CLASS_MAPPINGS = {
    "VisionModelLoaderTransformers": VisionModelLoaderTransformers,
    "VisionLanguageNodeTransformers": VisionLanguageNodeTransformers,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VisionModelLoaderTransformers": "🤖 Vision Model Loader (Transformers)",
    "VisionLanguageNodeTransformers": "🤖 Vision Language (Transformers)",
}
