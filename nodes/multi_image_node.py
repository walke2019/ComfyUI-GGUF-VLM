"""
Multi-Image Analysis Node - 多图像分析节点
支持输入多张图像进行对比分析
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
        TEXT_OUTPUT,
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
        TEXT_OUTPUT,
        merge_inputs
    )


class MultiImageAnalysis:
    """图像/视频分析节点（1 个视频 + 3 个图像输入）"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": merge_inputs(
                {
                    "model_config": ("TRANSFORMERS_MODEL",),
                    "prompt": (IO.STRING, {"default": "Describe these images.", "multiline": False, "tooltip": "用户提示词"}),
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
            "optional": {
                "video": ("IMAGE", {"tooltip": "视频帧序列或单张图像"}),
                "image_1": ("IMAGE", {"tooltip": "图像 1"}),
                "image_2": ("IMAGE", {"tooltip": "图像 2"}),
                "image_3": ("IMAGE", {"tooltip": "图像 3"}),
                "system_prompt": (
                    IO.STRING,
                    {
                        "default": "",
                        "multiline": True,
                        "tooltip": "系统提示词（可选）"
                    }
                ),
            }
        }
    
    RETURN_TYPES = TEXT_OUTPUT["types"]
    RETURN_NAMES = TEXT_OUTPUT["names"]
    FUNCTION = "analyze_images"
    CATEGORY = "🤖 GGUF-VLM/🖼️ Vision Models"
    OUTPUT_NODE = True
    
    def analyze_images(
        self,
        model_config,
        prompt,
        max_tokens,
        temperature,
        top_p,
        top_k,
        repetition_penalty,
        seed,
        video=None,
        image_1=None,
        image_2=None,
        image_3=None,
        system_prompt=""
    ):
        """分析图像或视频（1 个视频 + 最多 3 个图像）"""
        
        # 获取引擎
        from .vision_node_transformers import VisionModelLoaderTransformers
        engine = VisionModelLoaderTransformers._get_engine()
        
        # 确保模型已加载
        if engine.model is None or engine.processor is None:
            print("⚠️  Model not loaded, loading now...")
            success = engine.load_model(model_config)
            if not success:
                raise RuntimeError(f"Failed to load model: {model_config.get('model_name', 'unknown')}")
        
        # 收集所有输入的图像/视频
        images = []
        temp_paths = []
        
        # 首先处理视频输入（如果有）
        all_inputs = [video] if video is not None else []
        # 然后添加其他图像输入
        all_inputs.extend([image_1, image_2, image_3])
        
        for idx, image_tensor in enumerate(all_inputs, 1):
            if image_tensor is not None:
                # 检查是单帧图像还是视频帧序列
                num_frames = image_tensor.shape[0]
                
                if num_frames == 1:
                    # 单帧图像
                    pil_image = ToPILImage()(image_tensor[0].permute(2, 0, 1))
                    temp_path = Path(folder_paths.temp_directory) / f"multi_input_{seed}_{idx}.png"
                    pil_image.save(temp_path)
                    temp_paths.append(temp_path)
                    images.append(temp_path)
                    print(f"📸 Input {idx}: Single image")
                else:
                    # 视频帧序列：保存所有帧
                    print(f"📹 Input {idx}: Video with {num_frames} frames")
                    for frame_idx in range(num_frames):
                        pil_image = ToPILImage()(image_tensor[frame_idx].permute(2, 0, 1))
                        temp_path = Path(folder_paths.temp_directory) / f"multi_input_{seed}_{idx}_frame_{frame_idx:04d}.png"
                        pil_image.save(temp_path)
                        temp_paths.append(temp_path)
                        images.append(temp_path)
        
        if not images:
            raise ValueError("至少需要提供一个图像或视频输入")
        
        print(f"📸 Analyzing {len(images)} inputs (images/videos)")
        
        # 构建消息（Qwen3-VL 格式）
        messages = []
        
        # 构建用户消息内容（包含所有图像和文本）
        user_content = []
        
        # 添加所有图像
        for temp_path in temp_paths:
            user_content.append({
                "type": "image",
                "image": str(temp_path)
            })
        
        # 添加系统提示词（如果有）作为文本前缀
        if system_prompt and system_prompt.strip():
            user_content.append({
                "type": "text",
                "text": f"{system_prompt.strip()}\n\n{prompt}"
            })
        else:
            # 使用多图像分析的默认系统提示词
            default_prompt = (
                "You are an expert image analyst. When given multiple images, "
                "carefully compare and analyze them, identifying similarities, "
                "differences, patterns, and relationships between the images."
            )
            user_content.append({
                "type": "text",
                "text": f"{default_prompt}\n\n{prompt}"
            })
        
        messages.append({
            "role": "user",
            "content": user_content
        })
        
        # 执行推理
        try:
            result = engine.inference(
                messages=messages,
                temperature=temperature,
                max_new_tokens=max_tokens,
                top_p=top_p,
                top_k=top_k,
                repetition_penalty=repetition_penalty,
                seed=seed
            )
            
            print(f"✅ Analysis complete ({len(result)} chars)")
            print(f"   Images analyzed: {len(images)}")
            
            # 清理临时文件
            for temp_path in temp_paths:
                if temp_path.exists():
                    temp_path.unlink()
            
            # 如果不保持加载，卸载模型
            if not model_config.get("keep_loaded", False):
                engine.unload()
            
            return (result,)
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            import traceback
            traceback.print_exc()
            
            # 清理临时文件
            for temp_path in temp_paths:
                if temp_path.exists():
                    temp_path.unlink()
            
            raise


# 导出节点
NODE_CLASS_MAPPINGS = {
    "MultiImageAnalysis": MultiImageAnalysis,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MultiImageAnalysis": "🖼️ Image/Video Analysis (Transformers)",
}
