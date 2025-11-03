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
from comfy.comfy_types import IO

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
                            "Huihui-Qwen3-VL-8B-Instruct-abliterated"
                        ],
                        {
                            "default": "Huihui-Qwen3-VL-4B-Instruct-abliterated",
                            "tooltip": "选择 Qwen3-VL Abliterated 模型"
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
    CATEGORY = "🤖 GGUF-VLM/🖼️ Vision Models"
    
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
        elif model == "Huihui-Qwen3-VL-4B-Instruct-abliterated":
            model_id = "huihui-ai/Huihui-Qwen3-VL-4B-Instruct-abliterated"
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
                    "prompt": (IO.STRING, {"default": "Describe this image.", "multiline": False, "tooltip": "用户提示词"}),
                    "max_tokens": (
                        "INT",
                        {
                            "default": 512,
                            "min": 128,
                            "max": 256000,
                            "step": 1,
                            "tooltip": "最大生成 token 数"
                        }
                    ),
                },
                TEMPERATURE_INPUT,
                TOP_P_INPUT,
                TOP_K_INPUT,
                REPETITION_PENALTY_INPUT,
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
    CATEGORY = "🤖 GGUF-VLM/🖼️ Vision Models"
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
        
        # 准备图像或视频（支持多帧）
        temp_paths = []
        if image is not None:
            # 检查是单帧图像还是视频帧序列
            num_frames = image.shape[0]
            
            if num_frames == 1:
                # 单帧图像
                pil_image = ToPILImage()(image[0].permute(2, 0, 1))
                temp_path = Path(folder_paths.temp_directory) / f"temp_image_{seed}.png"
                pil_image.save(temp_path)
                temp_paths.append(temp_path)
                print(f"📸 Processing single image")
            else:
                # 视频帧序列：保存所有帧
                print(f"📹 Processing video with {num_frames} frames")
                for frame_idx in range(num_frames):
                    pil_image = ToPILImage()(image[frame_idx].permute(2, 0, 1))
                    temp_path = Path(folder_paths.temp_directory) / f"temp_video_{seed}_frame_{frame_idx:04d}.png"
                    pil_image.save(temp_path)
                    temp_paths.append(temp_path)
        
        # 构建消息（Qwen3-VL 格式 - 支持多帧视频分析）
        messages = []
        
        # 构建用户消息内容
        user_content = []
        
        # 添加所有图像/视频帧
        for temp_path in temp_paths:
            user_content.append({
                "type": "image",
                "image": str(temp_path)
            })
        
        # 处理提示词：如果有系统提示词，将其作为指令前缀添加到用户提示词中
        # 注意：不使用独立的 system role，而是合并到 user 消息中
        final_prompt = prompt
        if system_prompt and system_prompt.strip():
            # 系统提示词作为指令前缀
            final_prompt = f"{system_prompt.strip()}\n\n{prompt}"
        
        user_content.append({
            "type": "text",
            "text": final_prompt
        })
        
        messages.append({
            "role": "user",
            "content": user_content
        })
        
        # 执行推理（使用 Qwen3-VL 推荐参数）
        try:
            # 打印调试信息
            print(f"🔍 Generation parameters:")
            print(f"   - Prompt: {prompt[:100]}...")
            print(f"   - Temperature: {temperature}")
            print(f"   - Max tokens: {max_tokens}")
            print(f"   - Top-p: {top_p}")
            print(f"   - Top-k: {top_k}")
            print(f"   - Repetition penalty: {repetition_penalty}")
            
            # 限制 max_tokens 避免过长输出（但允许更长的描述）
            safe_max_tokens = min(max_tokens, 1024)
            if max_tokens > 1024:
                print(f"⚠️  Max tokens reduced from {max_tokens} to {safe_max_tokens} to prevent runaway generation")
            
            result = engine.inference(
                messages=messages,
                temperature=temperature,
                max_new_tokens=safe_max_tokens,
                seed=seed,
                top_p=top_p,
                top_k=top_k,
                repetition_penalty=repetition_penalty
            )
            
            print(f"✅ Generated text ({len(result)} chars)")
            print(f"📝 Output preview: {result[:200]}...")
            
            # 清理所有临时文件
            for temp_path in temp_paths:
                if temp_path.exists():
                    temp_path.unlink()
            
            # 如果不保持加载，卸载模型
            if not model_config.get("keep_loaded", False):
                engine.unload()
            
            return (result,)
            
        except Exception as e:
            print(f"❌ Generation failed: {e}")
            import traceback
            traceback.print_exc()
            
            # 清理临时文件
            for temp_path in temp_paths:
                if temp_path.exists():
                    temp_path.unlink()
            
            raise


# 导出节点
NODE_CLASS_MAPPINGS = {
    "VisionModelLoaderTransformers": VisionModelLoaderTransformers,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VisionModelLoaderTransformers": "🖼️ Vision Model Loader (Transformers)",
}
