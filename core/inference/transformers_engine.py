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

try:
    from config.paths import PathConfig
except ImportError:
    from ...config.paths import PathConfig


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
                from utils.download_manager import get_download_manager
                
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
                # 使用新的 API：processor.apply_chat_template
                # 不再需要 process_vision_info
                inputs = self.processor.apply_chat_template(
                    messages,
                    tokenize=True,
                    add_generation_prompt=True,
                    return_dict=True,
                    return_tensors="pt"
                )
                
                inputs = inputs.to(self.model.device)
                
                # 生成参数（遵循 Qwen3-VL 推荐）
                generation_config = {
                    "max_new_tokens": max_new_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                    "top_k": top_k,
                    "repetition_penalty": repetition_penalty,
                    "do_sample": temperature > 0,
                }
                
                # 生成
                generated_ids = self.model.generate(**inputs, **generation_config)
                
                # 解码
                generated_ids_trimmed = [
                    out_ids[len(in_ids):]
                    for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
                ]
                
                result = self.processor.batch_decode(
                    generated_ids_trimmed,
                    skip_special_tokens=True,
                    clean_up_tokenization_spaces=False,
                )
                
                return result[0] if result else ""
                
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
