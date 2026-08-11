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
from .core.backends import create_backend
from .core.inference.unified_api_engine import get_unified_api_engine
from .utils.streaming import sse_event


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
        
        # VL 主模型也可纯文本运行；文本列表只排除 mmproj/clip/projector 辅助文件
        helper_keywords = ['mmproj', 'clip', 'projector']
        local_models = [
            model_file for model_file in all_local_models
            if not any(keyword in model_file.lower() for keyword in helper_keywords)
        ]
        
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


@PromptServer.instance.routes.post("/gguf-vlm/stream-chat")
async def stream_chat(request):
    """
    Stream an OpenAI-compatible chat response as Server-Sent Events.

    JSON body:
        base_url, api_type, model, prompt, system_prompt, max_tokens, temperature
    """
    try:
        body = await request.json()
        base_url = body.get("base_url", "http://127.0.0.1:1234")
        api_type = body.get("api_type", "openai")
        model = body.get("model", "")
        prompt = body.get("prompt", "")
        system_prompt = body.get("system_prompt", "")
        max_tokens = int(body.get("max_tokens", 1024))
        temperature = float(body.get("temperature", 0.2))
        timeout = int(body.get("timeout", 300))

        response = web.StreamResponse(
            status=200,
            reason="OK",
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
        await response.prepare(request)

        engine = get_unified_api_engine(base_url, api_type)
        backend = create_backend(api_type, engine=engine)
        for delta in backend.stream_generate(
            model=model,
            prompt=prompt,
            image_urls=[],
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
        ):
            await response.write(sse_event(delta).encode("utf-8"))

        await response.write(sse_event("[DONE]").encode("utf-8"))
        await response.write_eof()
        return response
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)
