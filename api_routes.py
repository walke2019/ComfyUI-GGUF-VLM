"""
ComfyUI-GGUF-VLM API Routes
提供后端 API 端点，用于前端 JavaScript 调用
"""

import json
from aiohttp import web
from server import PromptServer
from .core.inference.nexa_engine import get_nexa_engine
from .core.model_loader import ModelLoader
from .utils.registry import RegistryManager


# 注册 API 路由
@PromptServer.instance.routes.get("/gguf-vlm/refresh-models")
async def refresh_models(request):
    """
    刷新远程 API 模型列表
    
    Query Parameters:
        base_url: API 服务地址
        api_type: API 类型 (ollama, nexa, openai)
    
    Returns:
        JSON: {"success": bool, "models": list, "error": str}
    """
    try:
        # 获取参数
        base_url = request.query.get('base_url', 'http://127.0.0.1:11434')
        api_type = request.query.get('api_type', 'ollama').lower()
        
        # 创建引擎并获取模型
        engine = get_nexa_engine(base_url)
        
        # 检查服务是否可用
        if not engine.is_service_available():
            return web.json_response({
                "success": False,
                "models": [],
                "error": f"Service not available at {base_url}"
            })
        
        # 获取模型列表
        models = engine.get_available_models(force_refresh=True)
        
        if not models:
            return web.json_response({
                "success": False,
                "models": [],
                "error": "No models found"
            })
        
        return web.json_response({
            "success": True,
            "models": models,
            "error": None
        })
        
    except Exception as e:
        return web.json_response({
            "success": False,
            "models": [],
            "error": str(e)
        })


# 刷新本地视觉模型列表
@PromptServer.instance.routes.get("/gguf-vlm/refresh-local-vision-models")
async def refresh_local_vision_models(request):
    """
    刷新本地视觉模型列表
    
    Returns:
        JSON: {"success": bool, "models": list, "error": str}
    """
    try:
        # 创建加载器和注册表
        loader = ModelLoader()
        registry = RegistryManager()
        
        # 获取所有本地模型
        all_local_models = loader.list_models()
        print(f"📦 Found {len(all_local_models)} local GGUF files")
        
        # 过滤视觉模型
        local_models = []
        for model_file in all_local_models:
            model_info = registry.find_model_by_filename(model_file)
            # 如果是视觉模型或未知模型（可能是视觉模型）
            if model_info is None or model_info.get('business_type') in ['image_analysis', 'video_analysis']:
                local_models.append(model_file)
        
        # 获取可下载的模型
        image_models = registry.get_downloadable_models(business_type='image_analysis', model_loader=loader)
        video_models = registry.get_downloadable_models(business_type='video_analysis', model_loader=loader)
        
        # 构建分类列表
        categorized_models = []
        
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
            return web.json_response({
                "success": False,
                "models": [],
                "error": "No vision models found"
            })
        
        return web.json_response({
            "success": True,
            "models": categorized_models,
            "error": None
        })
        
    except Exception as e:
        return web.json_response({
            "success": False,
            "models": [],
            "error": str(e)
        })


# 刷新本地文本模型列表
@PromptServer.instance.routes.get("/gguf-vlm/refresh-local-text-models")
async def refresh_local_text_models(request):
    """
    刷新本地文本模型列表
    
    Returns:
        JSON: {"success": bool, "models": list, "error": str}
    """
    try:
        # 创建加载器和注册表
        loader = ModelLoader()
        registry = RegistryManager()
        
        # 获取所有本地模型
        all_local_models = loader.list_models()
        print(f"📦 Found {len(all_local_models)} local GGUF files")
        
        # 视觉模型关键词列表（用于排除）
        vision_keywords = [
            'llava', 'vision', 'multimodal', 'mm', 
            'clip', 'minicpm-v', 'phi-3-vision', 
            'internvl', 'cogvlm', 'mmproj'
        ]
        
        # 特定的视觉模型模式
        vision_patterns = [
            'qwen-vl', 'qwen2-vl', 'qwen2.5-vl', 'qwen3-vl',
            '-vl-', '_vl_', '.vl.',
        ]
        
        # 过滤文本模型
        local_models = []
        for model_file in all_local_models:
            model_lower = model_file.lower()
            
            # 首先检查registry信息
            model_info = registry.find_model_by_filename(model_file)
            if model_info:
                business_type = model_info.get('business_type')
                if business_type == 'text_generation':
                    local_models.append(model_file)
                    continue
                elif business_type in ['image_analysis', 'video_analysis']:
                    continue
            
            # 使用关键词过滤
            is_vision_model = False
            for pattern in vision_patterns:
                if pattern in model_lower:
                    is_vision_model = True
                    break
            
            if not is_vision_model:
                is_vision_model = any(keyword in model_lower for keyword in vision_keywords)
            
            if not is_vision_model:
                local_models.append(model_file)
        
        # 获取可下载的文本模型
        downloadable = registry.get_downloadable_models(business_type='text_generation', model_loader=loader)
        downloadable_names = [name for name, _ in downloadable]
        
        # 合并列表
        all_models = local_models + downloadable_names
        
        if not all_models:
            return web.json_response({
                "success": False,
                "models": [],
                "error": "No text models found"
            })
        
        return web.json_response({
            "success": True,
            "models": all_models,
            "error": None
        })
        
    except Exception as e:
        return web.json_response({
            "success": False,
            "models": [],
            "error": str(e)
        })
