"""Simple model/backend recommendations for VLM workflows."""

from pathlib import Path

from .model_catalog import load_model_catalog, recommend_models


def recommend_vlm_setup(task: str, vram_gb: int, privacy: str = "本地优先") -> str:
    task_lower = (task or "").lower()
    privacy_lower = (privacy or "").lower()

    catalog_note = ""
    try:
        catalog = load_model_catalog(Path("model_catalog_v2.yaml"))
        catalog_task = "video" if ("video" in task_lower or "视频" in task_lower) else (
            "ocr" if ("ocr" in task_lower or "文字" in task_lower) else (
                "prompt_reverse" if ("prompt" in task_lower or "反推" in task_lower) else (
                    "json" if "json" in task_lower or "结构" in task_lower else "caption"
                )
            )
        )
        catalog_recs = recommend_models(catalog, catalog_task, vram_gb)
        if catalog_recs:
            top = catalog_recs[0]
            catalog_note = (
                f"\nModel Catalog 2.0（GGUF-first 能力目录）推荐: {top['id']} "
                f"(backend: {top.get('recommended_backend')}, min_vram: {top.get('min_vram_gb')}GB)"
            )
    except Exception:
        catalog_note = ""

    if "云" in privacy_lower or "remote" in privacy_lower:
        backend = "OpenAI-compatible remote API"
        model = "LM Studio / Ollama / llama.cpp server 中已加载的视觉模型"
    elif vram_gb >= 16:
        backend = "Local GGUF or llama.cpp server"
        model = "Qwen3-VL-8B-Instruct-GGUF Q4_K_M/Q8_0"
    elif vram_gb >= 8:
        backend = "Local GGUF Q4_K_M or LM Studio"
        model = "Qwen2.5-VL-3B/7B Q4 或 Qwen3-VL-8B Q4_K_M"
    else:
        backend = "Remote API / LM Studio CPU offload"
        model = "3B 级 VLM 或远程服务"

    if "ocr" in task_lower or "文字" in task_lower:
        note = "优先选择 Qwen3-VL GGUF/本地服务；InternVL/OCR VLM 作为远程或可选参考。"
    elif "video" in task_lower or "视频" in task_lower:
        note = "先用 Video Frame Sampler 抽帧，再送入远程/本地 VLM。"
    elif "caption" in task_lower or "标注" in task_lower:
        note = "使用 Caption Prompt Builder 的 数据集/标签 模式。"
    else:
        note = "使用 Remote VLM Business Task 的 Custom 模式微调提示词。"

    return f"推荐后端: {backend}\n推荐模型: {model}\n建议: {note}{catalog_note}"
