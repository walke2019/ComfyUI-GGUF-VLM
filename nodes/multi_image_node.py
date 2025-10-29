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
        PROMPT_INPUT,
        SYSTEM_PROMPT_INPUT,
        TEXT_OUTPUT,
        merge_inputs
    )


class MultiImageAnalysis:
    """多图像分析节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": merge_inputs(
                {
                    "model_config": ("TRANSFORMERS_MODEL",),
                },
                PROMPT_INPUT,
                TEMPERATURE_INPUT,
                {
                    "max_tokens": (
                        "INT",
                        {
                            "default": 2048,
                            "min": 128,
                            "max": 256000,
                            "step": 1,
                            "tooltip": "🤖 最大生成 token 数"
                        }
                    ),
                },
                SEED_INPUT
            ),
            "optional": {
                "image_1": ("IMAGE",),
                "image_2": ("IMAGE",),
                "image_3": ("IMAGE",),
                "image_4": ("IMAGE",),
                "image_5": ("IMAGE",),
                "image_6": ("IMAGE",),
                "system_prompt": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "tooltip": "🤖 系统提示词（可选）"
                    }
                ),
            }
        }
    
    RETURN_TYPES = TEXT_OUTPUT["types"]
    RETURN_NAMES = TEXT_OUTPUT["names"]
    FUNCTION = "analyze_images"
    CATEGORY = "🤖 GGUF-LLM/Multi-Image"
    OUTPUT_NODE = True
    
    def analyze_images(
        self,
        model_config,
        prompt,
        temperature,
        max_tokens,
        seed,
        image_1=None,
        image_2=None,
        image_3=None,
        image_4=None,
        image_5=None,
        image_6=None,
        system_prompt=""
    ):
        """分析多张图像"""
        
        # 获取引擎
        from .vision_node_transformers import VisionModelLoaderTransformers
        engine = VisionModelLoaderTransformers._get_engine()
        
        # 确保模型已加载
        if engine.model is None or engine.processor is None:
            print("⚠️  Model not loaded, loading now...")
            success = engine.load_model(model_config)
            if not success:
                raise RuntimeError(f"Failed to load model: {model_config.get('model_name', 'unknown')}")
        
        # 收集所有输入的图像
        images = []
        temp_paths = []
        
        for idx, image in enumerate([image_1, image_2, image_3, image_4, image_5, image_6], 1):
            if image is not None:
                pil_image = ToPILImage()(image[0].permute(2, 0, 1))
                temp_path = Path(folder_paths.temp_directory) / f"multi_image_{seed}_{idx}.png"
                pil_image.save(temp_path)
                temp_paths.append(temp_path)
                images.append(temp_path)
        
        if not images:
            raise ValueError("至少需要提供一张图像")
        
        print(f"📸 Analyzing {len(images)} images")
        
        # 构建消息（Qwen3-VL 格式）
        messages = []
        
        # 构建用户消息内容（包含所有图像和文本）
        user_content = []
        
        # 添加所有图像
        for temp_path in temp_paths:
            user_content.append({
                "type": "🤖 image",
                "image": str(temp_path)
            })
        
        # 添加系统提示词（如果有）作为文本前缀
        if system_prompt and system_prompt.strip():
            user_content.append({
                "type": "🤖 text",
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
                "type": "🤖 text",
                "text": f"{default_prompt}\n\n{prompt}"
            })
        
        messages.append({
            "role": "🤖 user",
            "content": user_content
        })
        
        # 执行推理
        try:
            result = engine.inference(
                messages=messages,
                temperature=temperature,
                max_new_tokens=max_tokens,
                top_p=0.8,
                top_k=20,
                repetition_penalty=1.0,
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


class MultiImageComparison:
    """多图像对比节点（预设提示词）"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_config": ("TRANSFORMERS_MODEL",),
                "comparison_type": (
                    [
                        "similarities - 找出相似之处",
                        "differences - 找出不同之处",
                        "changes - 分析变化",
                        "relationships - 分析关系",
                        "sequence - 分析顺序",
                        "quality - 质量对比",
                        "style - 风格对比",
                        "custom - 自定义",
                    ],
                    {
                        "default": "🤖 similarities - 找出相似之处",
                        "tooltip": "🤖 对比类型"
                    }
                ),
                "custom_prompt": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "tooltip": "🤖 自定义提示词（当选择 custom 时使用）"
                    }
                ),
                **TEMPERATURE_INPUT,
                **{
                    "max_tokens": (
                        "INT",
                        {
                            "default": 2048,
                            "min": 128,
                            "max": 256000,
                            "step": 1,
                            "tooltip": "🤖 最大生成 token 数"
                        }
                    ),
                },
                **SEED_INPUT,
            },
            "optional": {
                "image_1": ("IMAGE",),
                "image_2": ("IMAGE",),
                "image_3": ("IMAGE",),
                "image_4": ("IMAGE",),
                "image_5": ("IMAGE",),
                "image_6": ("IMAGE",),
            }
        }
    
    RETURN_TYPES = TEXT_OUTPUT["types"]
    RETURN_NAMES = TEXT_OUTPUT["names"]
    FUNCTION = "compare_images"
    CATEGORY = "🤖 GGUF-LLM/Multi-Image"
    OUTPUT_NODE = True
    
    # 预设提示词
    COMPARISON_PROMPTS = {
        "similarities": "🤖 Identify and describe the similarities between these images. Focus on common elements, themes, colors, compositions, and subjects.",
        "differences": "🤖 Identify and describe the differences between these images. Focus on what makes each image unique.",
        "changes": "🤖 Analyze the changes across these images. Describe what has changed from one image to the next.",
        "relationships": "🤖 Analyze the relationships between these images. How do they relate to each other? What story do they tell together?",
        "sequence": "🤖 Analyze these images as a sequence. Describe the progression or timeline they represent.",
        "quality": "🤖 Compare the quality of these images. Analyze aspects like resolution, clarity, composition, lighting, and technical execution.",
        "style": "🤖 Compare the artistic style of these images. Analyze the visual style, artistic techniques, and aesthetic choices.",
    }
    
    def compare_images(
        self,
        model_config,
        comparison_type,
        custom_prompt,
        temperature,
        max_tokens,
        seed,
        image_1=None,
        image_2=None,
        image_3=None,
        image_4=None,
        image_5=None,
        image_6=None
    ):
        """对比多张图像"""
        
        # 解析对比类型
        comp_key = comparison_type.split(" - ")[0]
        
        # 确定提示词
        if comp_key == "custom":
            if not custom_prompt or not custom_prompt.strip():
                raise ValueError("请提供自定义提示词")
            prompt = custom_prompt.strip()
        else:
            prompt = self.COMPARISON_PROMPTS.get(comp_key, self.COMPARISON_PROMPTS["similarities"])
        
        print(f"🔍 Comparison type: {comparison_type}")
        
        # 使用 MultiImageAnalysis 的逻辑
        analyzer = MultiImageAnalysis()
        return analyzer.analyze_images(
            model_config=model_config,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            seed=seed,
            image_1=image_1,
            image_2=image_2,
            image_3=image_3,
            image_4=image_4,
            image_5=image_5,
            image_6=image_6,
            system_prompt=""
        )


# 导出节点
NODE_CLASS_MAPPINGS = {
    "MultiImageAnalysis": MultiImageAnalysis,
    "MultiImageComparison": MultiImageComparison,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MultiImageAnalysis": "🤖 Multi-Image Analysis",
    "MultiImageComparison": "🤖 Multi-Image Comparison",
}
