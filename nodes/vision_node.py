"""
Vision Language Node - 视觉语言模型节点
"""

import os
import sys
import uuid
import numpy as np
from pathlib import Path
from PIL import Image
import folder_paths

# 添加父目录到路径
module_path = Path(__file__).parent.parent
if str(module_path) not in sys.path:
    sys.path.insert(0, str(module_path))

try:
    from core.model_loader import ModelLoader
    from core.inference_engine import InferenceEngine
    from core.cache_manager import CacheManager
    from utils.registry import RegistryManager
    from utils.downloader import FileDownloader
    from models.vision_models import VisionModelConfig, VisionModelPresets
    from utils.device_optimizer import DeviceOptimizer
    from utils.mmproj_validator import MMProjValidator
except ImportError as e:
    print(f"[ComfyUI-GGUF-VisionLM] Import error in vision_node: {e}")
    # 尝试相对导入
    from ..core.model_loader import ModelLoader
    from ..core.inference_engine import InferenceEngine
    from ..core.cache_manager import CacheManager
    from ..utils.registry import RegistryManager
    from ..utils.downloader import FileDownloader
    from ..models.vision_models import VisionModelConfig, VisionModelPresets
    from ..utils.device_optimizer import DeviceOptimizer
    from ..utils.mmproj_finder import MMProjFinder


class VisionModelLoader:
    """视觉语言模型加载器节点"""
    
    # 全局实例
    _model_loader = None
    _cache_manager = None
    _registry = None
    _device_optimizer = None
    
    @classmethod
    def _get_instances(cls):
        """获取全局实例"""
        if cls._model_loader is None:
            cls._model_loader = ModelLoader()
        if cls._cache_manager is None:
            cls._cache_manager = CacheManager()
        if cls._registry is None:
            cls._registry = RegistryManager()
        if cls._device_optimizer is None:
            cls._device_optimizer = DeviceOptimizer()
        return cls._model_loader, cls._cache_manager, cls._registry, cls._device_optimizer
    
    @classmethod
    def INPUT_TYPES(cls):
        loader, cache, registry, optimizer = cls._get_instances()
        
        # 获取本地模型
        all_local_models = loader.list_models()
        
        # 过滤本地模型：只显示视觉语言类型的模型
        local_models = []
        for model_file in all_local_models:
            model_info = registry.find_model_by_filename(model_file)
            # 如果找到模型信息且是图像/视频分析类型，或者找不到信息（未知模型，保留）
            if model_info is None or model_info.get('business_type') in ['image_analysis', 'video_analysis']:
                local_models.append(model_file)
        
        # 获取不同类型的可下载模型
        image_models = registry.get_downloadable_models(business_type='image_analysis')
        video_models = registry.get_downloadable_models(business_type='video_analysis')
        
        # 添加类型标签
        categorized_models = []
        
        # 添加分组标题
        if image_models:
            categorized_models.append("--- 🖼️ 图像分析模型 ---")
            categorized_models.extend([name for name, _ in image_models])
        
        if video_models:
            categorized_models.append("--- 🎥 视频分析模型 ---")
            categorized_models.extend([name for name, _ in video_models])
        
        if local_models:
            categorized_models.append("--- 💾 本地模型 ---")
            categorized_models.extend(local_models)
        
        if not categorized_models:
            categorized_models = ["No models found"]
        
        return {
            "required": {
                "model": (categorized_models, {
                    "default": categorized_models[0] if categorized_models else "No models found",
                    "tooltip": "🤖 选择视觉语言模型（按类型分组）"
                }),
                "n_ctx": ("INT", {
                    "default": 8192,
                    "min": 512,
                    "max": 32768,
                    "step": 512,
                    "tooltip": "🤖 上下文窗口大小"
                }),
                "device": (["Auto", "GPU", "CPU"], {
                    "default": "🤖 Auto",
                    "tooltip": "🤖 运行设备 (Auto=自动检测, GPU=全部GPU, CPU=仅CPU)"
                }),
            },
            "optional": {
                "mmproj_file": ("STRING", {
                    "default": "",
                    "tooltip": "🤖 手动指定 mmproj 文件（可选）"
                }),
            }
        }
    
    RETURN_TYPES = ("VISION_MODEL",)
    RETURN_NAMES = ("model",)
    FUNCTION = "load_model"
    CATEGORY = "🤖 GGUF-LLM/Vision"
    
    def load_model(self, model, n_ctx=8192, device="Auto", mmproj_file=""):
        """加载视觉语言模型"""
        loader, cache, registry, optimizer = self._get_instances()
        
        # 检查 llama-cpp-python 安装状态
        llama_status = optimizer.check_llama_cpp_installation()
        if not llama_status['installed']:
            error_msg = "❌ llama-cpp-python not installed.\n"
            error_msg += "Install with:\n"
            error_msg += "  pip install llama-cpp-python\n"
            error_msg += "\nFor CUDA support, see: /home/README_LLAMA_CPP_INSTALL.md"
            raise RuntimeError(error_msg)
        
        if llama_status['issues']:
            for issue in llama_status['issues']:
                print(f"⚠️  {issue}")
        
        # 显示设备信息
        device_summary = optimizer.get_device_summary()
        print(f"\n{device_summary}\n")
        
        # 根据设备选项设置参数
        if device == "Auto":
            # 使用智能优化
            optimized_params = optimizer.get_optimized_params(model_size_gb=7.0)
            n_gpu_layers = optimized_params['n_gpu_layers']
            n_batch = optimized_params.get('n_batch', 512)
            
            print(f"🎯 Auto-optimized: {optimized_params['device_info']}")
            print(f"   GPU layers: {n_gpu_layers}")
            print(f"   Batch size: {n_batch}")
        elif device == "GPU":
            n_gpu_layers = -1
            n_batch = 512
            print(f"🎮 Using GPU (all layers)")
        else:  # CPU
            n_gpu_layers = 0
            n_batch = 128
            print(f"💻 Using CPU only")
        
        # 检查是否是分组标题
        if model.startswith("---"):
            raise ValueError("请选择一个具体的模型，而不是分组标题")
        
        print(f"📦 加载模型: {model}")
        
        # 检查是否需要下载
        if model.startswith("[⬇️"):
            print(f"📥 Model needs to be downloaded: {model}")
            download_info = registry.get_model_download_info(model)
            
            if download_info:
                downloader = FileDownloader()
                model_dir = loader.model_dirs[0]
                
                # 下载模型文件
                downloaded_path = downloader.download_from_huggingface(
                    repo_id=download_info['repo'],
                    filename=download_info['filename'],
                    dest_dir=model_dir
                )
                
                if not downloaded_path:
                    raise RuntimeError(f"Failed to download model: {model}")
                
                # 下载 mmproj 文件
                if download_info.get('mmproj'):
                    # 使用 mmproj_repo（如果指定）或默认使用模型仓库
                    mmproj_repo = download_info.get('mmproj_repo', download_info['repo'])
                    mmproj_downloaded = downloader.download_from_huggingface(
                        repo_id=mmproj_repo,
                        filename=download_info['mmproj'],
                        dest_dir=model_dir
                    )
                    if mmproj_downloaded:
                        mmproj_file = download_info['mmproj']
                        print(f"✅ Downloaded mmproj from {mmproj_repo}")
                
                model = download_info['filename']
                cache.clear("new model downloaded")
            else:
                raise ValueError(f"Cannot find download info for: {model}")
        
        # 查找模型路径
        model_path = loader.find_model(model)
        if not model_path:
            raise FileNotFoundError(f"Model not found: {model}")
        
        # 查找 mmproj 文件
        mmproj_path = None
        if mmproj_file:
            # 手动指定
            mmproj_path = loader.find_mmproj(model, mmproj_file)
            if not mmproj_path:
                raise FileNotFoundError(f"mmproj file not found: {mmproj_file}")
        else:
            # 自动查找 - 直接使用智能查找器
            print(f"🔍 Auto-searching for mmproj file...")
            mmproj_path = loader.find_mmproj(model)  # 不传 mmproj_name，让它自动查找
            
            if not mmproj_path:
                # 尝试通过 registry 查找
                mmproj_name = registry.smart_match_mmproj(model)
                if mmproj_name:
                    mmproj_path = loader.find_mmproj(model, mmproj_name)
                
                if not mmproj_path:
                    print(f"⚠️  mmproj not found locally, attempting auto-download...")
                    # 尝试自动下载
                    model_info = registry.find_model_by_filename(model)
                    if model_info and model_info.get('mmproj'):
                        downloader = FileDownloader()
                        model_dir = os.path.dirname(model_path)
                        mmproj_path = downloader.download_from_huggingface(
                            repo_id=model_info['repo'],
                            filename=model_info['mmproj'],
                            dest_dir=model_dir
                        )
        
        if not mmproj_path:
            # 使用智能查找器和验证器
            from ..utils.mmproj_finder import MMProjFinder
            from ..utils.mmproj_validator import MMProjValidator
            
            finder = MMProjFinder([os.path.dirname(model_path)])
            validator = MMProjValidator()
            
            # 获取建议
            suggestions = validator.suggest_mmproj_for_model(model)
            available = finder.list_all_mmproj_files(os.path.dirname(model_path))
            
            error_msg = f"❌ Could not find mmproj file for {model}.\n\n"
            
            # 显示主要建议
            error_msg += f"💡 Recommended mmproj filename:\n"
            error_msg += f"   {suggestions['primary']}\n\n"
            
            if suggestions['notes']:
                error_msg += f"📝 Note: {suggestions['notes']}\n\n"
            
            # 显示可用文件并检查兼容性
            if available:
                error_msg += f"📁 Available mmproj files in model directory:\n"
                for mmproj_path_item in available:
                    mmproj_name = os.path.basename(mmproj_path_item)
                    
                    # 检查兼容性
                    compat = validator.check_compatibility(model, mmproj_name)
                    
                    if compat['confidence'] == 'high':
                        error_msg += f"   ✅ {mmproj_name} (推荐使用)\n"
                    elif compat['confidence'] == 'medium':
                        error_msg += f"   ⚠️  {mmproj_name} (可能兼容)\n"
                    else:
                        error_msg += f"   ❌ {mmproj_name} (可能不兼容)\n"
                    
                    # 显示警告
                    if compat['warnings']:
                        for warning in compat['warnings']:
                            error_msg += f"      ⚠️  {warning}\n"
                
                error_msg += "\n"
            
            error_msg += "⚠️  重要提示:\n"
            error_msg += "   - mmproj 文件必须与模型的视觉编码器匹配\n"
            error_msg += "   - 不同版本的模型可能需要不同的 mmproj 文件\n"
            error_msg += "   - 使用不匹配的 mmproj 会导致张量错误\n\n"
            
            error_msg += "解决方案:\n"
            error_msg += "1. 下载与模型匹配的 mmproj 文件\n"
            error_msg += "2. 如果有推荐的文件，重命名为推荐的文件名\n"
            error_msg += "3. 在节点中手动指定 mmproj_file 参数\n"
            
            raise FileNotFoundError(error_msg)
        
        # 应用预设配置
        preset = VisionModelPresets.get_preset(model)
        if preset:
            print(f"📋 Applying preset for {model}")
            if n_ctx == 8192:  # 如果是默认值，使用预设
                n_ctx = preset.get('n_ctx', n_ctx)
        
        # 创建配置
        config = VisionModelConfig(
            model_name=model,
            model_path=model_path,
            mmproj_path=mmproj_path,
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers
        )
        
        # 验证配置
        validation = config.validate()
        if not validation['valid']:
            raise ValueError(f"Invalid config: {validation['errors']}")
        
        print(f"✅ Vision model loaded: {model}")
        print(f"📁 Using mmproj: {os.path.basename(mmproj_path)}")
        
        return (config.to_dict(),)


class VisionLanguageNode:
    """视觉语言生成节点"""
    
    # 全局推理引擎
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
                "model": ("VISION_MODEL", {
                    "tooltip": "🤖 视觉语言模型配置"
                }),
                "prompt": ("STRING", {
                    "default": "🤖 Describe this image in detail.",
                    "multiline": True,
                    "tooltip": "🤖 用户提示词"
                }),
                "max_tokens": ("INT", {
                    "default": 512,
                    "min": 1,
                    "max": 4096,
                    "step": 1,
                    "tooltip": "🤖 最大生成 token 数"
                }),
                "temperature": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.1,
                    "tooltip": "🤖 温度参数"
                }),
                "top_p": ("FLOAT", {
                    "default": 0.9,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.05,
                    "tooltip": "🤖 Top-p 采样"
                }),
                "top_k": ("INT", {
                    "default": 40,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                    "tooltip": "🤖 Top-k 采样"
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xFFFFFFFFFFFFFFFF,
                    "tooltip": "🤖 随机种子"
                }),
            },
            "optional": {
                "image": ("IMAGE", {
                    "tooltip": "🤖 输入图像（与视频二选一）"
                }),
                "video": ("IMAGE", {
                    "tooltip": "🤖 输入视频帧序列（与图像二选一）"
                }),
                "system_prompt": ("STRING", {
                    "default": "🤖 You are a helpful assistant that describes images and videos accurately and in detail.",
                    "multiline": True,
                    "tooltip": "🤖 系统提示词（可自定义模型行为）"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("context",)
    FUNCTION = "describe_image"
    CATEGORY = "🤖 GGUF-LLM/Vision"
    OUTPUT_NODE = True
    
    def describe_image(self, model, prompt, max_tokens=512, 
                      temperature=0.7, top_p=0.9, top_k=40, seed=0,
                      image=None, video=None, system_prompt=None):
        """生成图像/视频描述"""
        try:
            from llama_cpp import Llama
            from llama_cpp.llama_chat_format import Qwen25VLChatHandler
            
            # 验证输入：必须提供图像或视频之一
            if image is None and video is None:
                raise ValueError("必须提供 image 或 video 输入之一")
            if image is not None and video is not None:
                raise ValueError("不能同时提供 image 和 video 输入，请只选择一个")
            
            engine = self._get_engine()
            model_path = model['model_path']
            mmproj_path = model['mmproj_path']
            
            # 确定输入类型
            is_video = video is not None
            input_data = video if is_video else image
            
            print(f"📊 输入类型: {'视频' if is_video else '图像'}")
            if is_video:
                print(f"🎬 视频帧数: {input_data.shape[0]}")
            
            # 加载模型（如果未加载）
            if not engine.is_model_loaded(model_path):
                print(f"🔄 Loading vision model into memory...")
                print(f"📁 Model: {os.path.basename(model_path)}")
                print(f"📁 mmproj: {os.path.basename(mmproj_path)}")
                
                chat_handler = Qwen25VLChatHandler(clip_model_path=mmproj_path)
                llm = Llama(
                    model_path=model_path,
                    chat_handler=chat_handler,
                    n_ctx=model.get('n_ctx', 8192),
                    n_gpu_layers=model.get('n_gpu_layers', -1),
                    verbose=model.get('verbose', False),
                    seed=seed
                )
                
                engine.loaded_models[model_path] = llm
                print(f"✅ Vision model loaded successfully")
            else:
                llm = engine.loaded_models[model_path]
            
            # 处理图像或视频帧
            if is_video:
                # 视频：保存多个帧
                image_paths = self._save_video_frames(input_data, seed)
            else:
                # 图像：保存单帧
                image_paths = [self._save_temp_image(input_data, seed)]
            
            # 构建消息内容
            content = []
            
            # 添加图像/视频帧
            for img_path in image_paths:
                content.append({
                    "type": "🤖 image_url",
                    "image_url": {"url": f"file://{img_path}"}
                })
            
            # 添加用户提示词
            content.append({
                "type": "🤖 text",
                "text": prompt
            })
            
            # 构建消息列表
            messages = []
            
            # 添加系统提示词（如果提供）
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
                print(f"📋 系统提示词: {system_prompt[:50]}...")
            
            messages.append({"role": "user", "content": content})
            
            print(f"🤖 Generating {'video' if is_video else 'image'} description...")
            print(f"📝 用户提示词: {prompt[:50]}...")
            
            # 生成描述
            response = llm.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                stream=False
            )
            
            output_text = response["choices"][0]["message"]["content"]
            
            # 清理临时文件
            for img_path in image_paths:
                try:
                    os.remove(img_path)
                except:
                    pass
            
            print(f"✅ Generated description ({len(output_text)} chars)")
            return (str(output_text),)
        
        except ImportError as e:
            error_msg = "❌ llama-cpp-python not installed. Install with: pip install llama-cpp-python"
            print(error_msg)
            return (error_msg,)
        
        except Exception as e:
            import traceback
            error_msg = f"❌ Error: {str(e)}"
            print(f"❌ Detailed error:\n{traceback.format_exc()}")
            return (error_msg,)
    
    def _save_temp_image(self, image, seed):
        """保存图像到临时文件"""
        unique_id = uuid.uuid4().hex
        image_path = Path(folder_paths.temp_directory) / f"temp_image_{seed}_{unique_id}.png"
        image_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 转换 tensor 到 PIL Image
        img_array = image.cpu().numpy()
        if img_array.ndim == 4:
            img_array = img_array[0]  # 取第一张图像
        img_array = np.clip(255.0 * img_array, 0, 255).astype(np.uint8)
        img = Image.fromarray(img_array)
        img.save(str(image_path))
        
        return str(image_path.resolve())
    
    def _save_video_frames(self, video, seed, max_frames=8):
        """保存视频帧到临时文件"""
        unique_id = uuid.uuid4().hex
        temp_dir = Path(folder_paths.temp_directory) / f"temp_video_{seed}_{unique_id}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 转换 tensor 到 PIL Images
        video_array = video.cpu().numpy()
        num_frames = video_array.shape[0]
        
        print(f"🎬 处理视频: {num_frames} 帧")
        
        # 采样帧（如果帧数太多）
        if num_frames > max_frames:
            indices = np.linspace(0, num_frames - 1, max_frames, dtype=int)
            video_array = video_array[indices]
            print(f"📊 采样到 {max_frames} 帧")
        
        image_paths = []
        for i, frame in enumerate(video_array):
            img_array = np.clip(255.0 * frame, 0, 255).astype(np.uint8)
            img = Image.fromarray(img_array)
            
            frame_path = temp_dir / f"frame_{i:04d}.png"
            img.save(str(frame_path))
            image_paths.append(str(frame_path.resolve()))
        
        print(f"✅ 保存了 {len(image_paths)} 个视频帧")
        return image_paths


# 节点注册
NODE_CLASS_MAPPINGS = {
    "VisionModelLoader": VisionModelLoader,
    "VisionLanguageNode": VisionLanguageNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VisionModelLoader": "🤖 Vision Model Loader",
    "VisionLanguageNode": "🤖 Vision Language Generation",
}
