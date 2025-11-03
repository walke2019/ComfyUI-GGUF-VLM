"""
Transformers Inference Engine - 基于 Transformers 的推理引擎
支持 Qwen3-VL 等 Transformers 模型（使用最新 API）
"""

import os
import sys
import torch
import shutil
from typing import Dict, Optional, List, Any
from pathlib import Path

# 添加父目录到路径
module_path = Path(__file__).parent.parent.parent
if str(module_path) not in sys.path:
    sys.path.insert(0, str(module_path))

# 导入配置和工具（ComfyUI 环境兼容）
try:
    # 方式1: 尝试从当前包导入
    from config.paths import PathConfig
    from utils.download_manager import get_download_manager
except ImportError:
    try:
        # 方式2: 尝试相对导入
        from ...config.paths import PathConfig
        from ...utils.download_manager import get_download_manager
    except (ImportError, ValueError):
        # 方式3: 动态导入（最可靠）
        import importlib.util
        
        # 导入 PathConfig
        paths_file = module_path / 'config' / 'paths.py'
        spec = importlib.util.spec_from_file_location('config.paths', paths_file)
        paths_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(paths_module)
        PathConfig = paths_module.PathConfig
        
        # 导入 get_download_manager
        dm_file = module_path / 'utils' / 'download_manager.py'
        spec = importlib.util.spec_from_file_location('utils.download_manager', dm_file)
        dm_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dm_module)
        get_download_manager = dm_module.get_download_manager


class TransformersInferenceEngine:
    """Transformers 推理引擎（Qwen3-VL 优化版）"""
    
    def __init__(self):
        self.model = None
        self.processor = None
        self.current_model_id = None
        self.current_config = None
        
    def load_model(self, config: Dict) -> bool:
        """
        加载模型
        
        Args:
            config: 模型配置
                - model_name: 模型名称
                - model_id: HuggingFace 模型 ID
                - quantization: 量化类型 (none/4bit/8bit)
                - attention: 注意力机制 (eager/sdpa/flash_attention_2)
                - device: 设备
                - dtype: 数据类型
                - min_pixels: 最小像素
                - max_pixels: 最大像素
        
        Returns:
            是否成功加载
        """
        try:
            from transformers import (
                AutoModelForVision2Seq,
                AutoProcessor,
                BitsAndBytesConfig,
            )
            
            # 尝试导入 Qwen3VL 特定类（如果可用）
            try:
                from transformers import Qwen3VLForConditionalGeneration
                use_qwen3vl = True
            except ImportError:
                use_qwen3vl = False
                print("⚠️  Qwen3VLForConditionalGeneration not available, using AutoModelForVision2Seq")
            import comfy.model_management
            
            model_id = config.get('model_id')
            model_name = config.get('model_name', model_id)
            
            # 检查是否需要重新加载
            if (self.current_model_id == model_id and 
                self.current_config == config and
                self.model is not None and 
                self.processor is not None):
                print(f"✅ Model already loaded: {model_name}")
                return True
            
            # 清理旧模型
            if self.model is not None or self.processor is not None:
                self._unload_model()
            
            # 使用统一的路径配置
            model_checkpoint = PathConfig.get_model_path("llm", model_id)
            
            # 下载模型（如果需要）
            # 检查关键文件是否存在
            key_files = [
                "config.json",
                "model.safetensors.index.json",
            ]
            
            needs_download = not os.path.exists(model_checkpoint)
            if os.path.exists(model_checkpoint):
                # 检查是否有关键文件缺失
                for key_file in key_files:
                    if not os.path.exists(os.path.join(model_checkpoint, key_file)):
                        needs_download = True
                        print(f"⚠️ Missing key file: {key_file}, will re-download")
                        break
            
            if needs_download:
                download_manager = get_download_manager()
                
                # 检查磁盘空间
                if not download_manager.check_disk_space(model_checkpoint, required_gb=10.0):
                    raise RuntimeError("Insufficient disk space for model download")
                
                # 下载模型
                success = download_manager.download_repository(
                    repo_id=model_id,
                    local_dir=model_checkpoint,
                    ignore_patterns=[
                        "*.gguf",
                        "GGUF/*",
                        "*.bin",
                        "*.msgpack",
                    ],
                    resume=True
                )
                
                if not success:
                    raise RuntimeError(f"Failed to download model: {model_id}")
            
            # 加载 Processor（Qwen3-VL 不需要 min_pixels/max_pixels 参数）
            print(f"📦 Loading processor from: {model_checkpoint}")
            self.processor = AutoProcessor.from_pretrained(model_checkpoint)
            
            # 配置量化
            quantization = config.get('quantization', 'none')
            quantization_config = None
            
            if quantization == '4bit':
                quantization_config = BitsAndBytesConfig(load_in_4bit=True)
                print("🔧 Using 4-bit quantization")
            elif quantization == '8bit':
                quantization_config = BitsAndBytesConfig(load_in_8bit=True)
                print("🔧 Using 8-bit quantization")
            
            # 确定数据类型
            device = comfy.model_management.get_torch_device()
            bf16_support = (
                torch.cuda.is_available() and
                torch.cuda.get_device_capability(device)[0] >= 8
            )
            dtype = torch.bfloat16 if bf16_support else torch.float16
            
            # 加载模型
            print(f"📦 Loading model: {model_name}")
            attention = config.get('attention', 'sdpa')
            
            # Qwen3-VL 推荐使用 flash_attention_2
            if attention == 'flash_attention_2':
                print("⚡ Using Flash Attention 2 (recommended for Qwen3-VL)")
            
            model_kwargs = {
                "dtype": dtype,
                "device_map": "auto",
            }
            
            # 只在非量化时添加 attn_implementation
            if quantization == 'none':
                model_kwargs["attn_implementation"] = attention
            
            if quantization_config:
                model_kwargs["quantization_config"] = quantization_config
            
            # 根据可用性选择模型类
            ModelClass = Qwen3VLForConditionalGeneration if use_qwen3vl else AutoModelForVision2Seq
            
            self.model = ModelClass.from_pretrained(
                model_checkpoint,
                **model_kwargs
            )
            
            self.current_model_id = model_id
            self.current_config = config.copy()
            
            print(f"✅ Model loaded successfully: {model_name}")
            print(f"   Location: {model_checkpoint}")
            print(f"   Device: {device}")
            print(f"   Dtype: {dtype}")
            print(f"   Attention: {attention}")
            print(f"   Quantization: {quantization}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def inference(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        max_new_tokens: int = 2048,
        seed: int = 0,
        top_p: float = 0.8,
        top_k: int = 20,
        repetition_penalty: float = 1.0
    ) -> str:
        """
        执行推理（使用 Qwen3-VL 新 API）
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_new_tokens: 最大生成 token 数
            seed: 随机种子
            top_p: nucleus sampling 参数
            top_k: top-k sampling 参数
            repetition_penalty: 重复惩罚
        
        Returns:
            生成的文本
        """
        if self.model is None or self.processor is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        try:
            # 设置随机种子
            if seed > 0:
                torch.manual_seed(seed)
                if torch.cuda.is_available():
                    torch.cuda.manual_seed_all(seed)
            
            with torch.no_grad():
                # 使用 1038lab/ComfyUI-QwenVL 的方式：先生成文本提示，再处理图像
                # Step 1: 生成文本提示（不 tokenize）
                text_prompt = self.processor.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True
                )
                
                # Step 2: 提取图像
                pil_images = []
                for msg in messages:
                    if isinstance(msg.get('content'), list):
                        for item in msg['content']:
                            if item.get('type') == 'image':
                                # 图像已经是 PIL Image 或路径
                                from PIL import Image
                                img = item.get('image')
                                if isinstance(img, str):
                                    pil_images.append(Image.open(img))
                                elif isinstance(img, Image.Image):
                                    pil_images.append(img)
                
                # Step 3: 使用 processor 处理文本和图像
                inputs = self.processor(
                    text=text_prompt,
                    images=pil_images if pil_images else None,
                    return_tensors="pt"
                )
                
                # 移动到设备
                model_inputs = {k: v.to(self.model.device) for k, v in inputs.items() if torch.is_tensor(v)}
                
                # 生成参数（遵循 1038lab/ComfyUI-QwenVL 的方式）
                stop_tokens = [self.processor.tokenizer.eos_token_id]
                if hasattr(self.processor.tokenizer, 'eot_id'):
                    stop_tokens.append(self.processor.tokenizer.eot_id)
                
                generation_config = {
                    "max_new_tokens": max_new_tokens,
                    "repetition_penalty": repetition_penalty,
                    "eos_token_id": stop_tokens,
                    "pad_token_id": self.processor.tokenizer.pad_token_id,
                    "do_sample": temperature > 0,
                    "temperature": temperature if temperature > 0 else None,
                    "top_p": top_p if temperature > 0 else None,
                    "top_k": top_k if temperature > 0 else None,
                }
                
                # 移除 None 值
                generation_config = {k: v for k, v in generation_config.items() if v is not None}
                
                print(f"🔍 Inference config: temp={temperature}, max_tokens={max_new_tokens}, top_p={top_p}, rep_penalty={repetition_penalty}")
                
                # 生成
                generated_ids = self.model.generate(**model_inputs, **generation_config)
                
                # 解码（只解码新生成的 tokens）
                input_ids_len = model_inputs["input_ids"].shape[1]
                generated_text = self.processor.tokenizer.decode(
                    generated_ids[0, input_ids_len:],
                    skip_special_tokens=True
                )
                
                return generated_text.strip()
                
        except Exception as e:
            print(f"❌ Inference failed: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _unload_model(self):
        """卸载模型"""
        if self.processor is not None:
            del self.processor
            self.processor = None
        
        if self.model is not None:
            del self.model
            self.model = None
        
        self.current_model_id = None
        self.current_config = None
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        
        print("🗑️  Model unloaded")
    
    def _check_disk_space(self, path: str, required_gb: float = 15):
        """检查磁盘空间"""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            total, used, free = shutil.disk_usage(os.path.dirname(path))
            free_gb = free / (1024**3)
            
            if free_gb < required_gb:
                raise RuntimeError(
                    f"Insufficient disk space. Required: {required_gb}GB, "
                    f"Available: {free_gb:.1f}GB"
                )
        except Exception as e:
            print(f"⚠️  Could not check disk space: {e}")
    
    def unload(self):
        """公开的卸载方法"""
        self._unload_model()
