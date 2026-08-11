"""Business-oriented VLM nodes: caption, OCR, prompt reverse, JSON, video sampling."""

import base64
from io import BytesIO
from typing import Any, Dict

import numpy as np
from PIL import Image
from comfy.comfy_types import IO

from ..core.backends import create_backend
from ..core.inference.unified_api_engine import get_unified_api_engine
from ..utils.business_prompts import (
    build_caption_prompt,
    build_json_prompt,
    build_ocr_prompt,
    build_prompt_reverse_prompt,
)
from ..utils.model_advisor import recommend_vlm_setup
from ..utils.node_metadata import build_v3_node_metadata
from ..utils.json_schema_tools import validate_json_fields
from ..utils.batch_utils import build_batch_labels
from ..utils.video_utils import select_frame_indices


def image_to_data_url(image) -> str:
    """Convert a ComfyUI IMAGE tensor/batch to a PNG data URL."""
    img_array = image.cpu().numpy()
    if img_array.ndim == 4:
        img_array = img_array[0]
    img_array = np.clip(255.0 * img_array, 0, 255).astype(np.uint8)
    pil_image = Image.fromarray(img_array)
    buffer = BytesIO()
    pil_image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


class CaptionPromptBuilder:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "style": (["详细", "简洁", "标签", "电商", "数据集"], {"default": "详细"}),
                "language": (["中文", "English", "日本語", "한국어"], {"default": "中文"}),
                "domain": (IO.STRING, {"default": "通用", "multiline": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "build"
    CATEGORY = "🤖 GGUF-VLM/🚀 Business"

    def build(self, style="详细", language="中文", domain="通用"):
        return (build_caption_prompt(style, language, domain),)


class OCRPromptBuilder:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "language": (["中文", "English", "原文"], {"default": "原文"}),
                "output_format": (["按行", "表格", "JSON"], {"default": "按行"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "build"
    CATEGORY = "🤖 GGUF-VLM/🚀 Business"

    def build(self, language="原文", output_format="按行"):
        return (build_ocr_prompt(language, output_format),)


class PromptReverseBuilder:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "target": (["Stable Diffusion", "Flux", "SDXL", "Midjourney"], {"default": "Stable Diffusion"}),
                "language": (["English", "中文"], {"default": "English"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "build"
    CATEGORY = "🤖 GGUF-VLM/🚀 Business"

    def build(self, target="Stable Diffusion", language="English"):
        return (build_prompt_reverse_prompt(target, language),)


class JSONPromptBuilder:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "task": (IO.STRING, {"default": "识别主体、动作、场景、风格和可见文字", "multiline": True}),
                "schema": (IO.STRING, {"default": "subject, action, scene, style, text, tags", "multiline": True}),
                "language": (["中文", "English"], {"default": "中文"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "build"
    CATEGORY = "🤖 GGUF-VLM/🚀 Business"

    def build(self, task, schema, language="中文"):
        return (build_json_prompt(task, schema, language),)


class RemoteVLMTaskRunner:
    """Run a business task against a configured remote VLM."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_config": ("REMOTE_VISION_MODEL", {}),
                "task": (["Caption", "OCR", "Prompt Reverse", "JSON", "Custom"], {"default": "Caption"}),
                "max_tokens": ("INT", {"default": 1024, "min": 1, "max": 8192, "step": 1}),
                "temperature": ("FLOAT", {"default": 0.2, "min": 0.0, "max": 2.0, "step": 0.1}),
                "timeout": ("INT", {"default": 300, "min": 30, "max": 1800, "step": 30}),
            },
            "optional": {
                "image": ("IMAGE", {}),
                "custom_prompt": (IO.STRING, {"default": "", "multiline": True}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result",)
    FUNCTION = "run"
    CATEGORY = "🤖 GGUF-VLM/🚀 Business"
    OUTPUT_NODE = True

    def _default_prompt(self, task: str) -> str:
        if task == "Caption":
            return build_caption_prompt("详细", "中文", "通用")
        if task == "OCR":
            return build_ocr_prompt("原文", "按行")
        if task == "Prompt Reverse":
            return build_prompt_reverse_prompt("Stable Diffusion", "English")
        if task == "JSON":
            return build_json_prompt("识别主体、动作、场景、风格和文字", "subject, action, scene, style, text, tags")
        return "Describe the input accurately."

    def run(
        self,
        model_config: Dict[str, Any],
        task: str,
        max_tokens: int = 1024,
        temperature: float = 0.2,
        timeout: int = 300,
        image=None,
        custom_prompt: str = "",
    ):
        if not model_config.get("service_available", False):
            return (f"❌ 服务不可用: {model_config.get('base_url', 'unknown')}",)

        prompt = custom_prompt.strip() or self._default_prompt(task)
        image_urls = [image_to_data_url(image)] if image is not None else []

        engine = get_unified_api_engine(model_config["base_url"], model_config["api_type"])
        backend = create_backend(model_config["api_type"], engine=engine)
        result = backend.generate(
            model=model_config.get("model_name", ""),
            prompt=prompt,
            image_urls=image_urls,
            system_prompt=model_config.get("system_prompt", ""),
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
        )
        return (result,)


class VideoFrameSampler:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video": ("IMAGE", {}),
                "max_frames": ("INT", {"default": 8, "min": 1, "max": 64, "step": 1}),
                "strategy": (["uniform", "head", "tail"], {"default": "uniform"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("frames", "indices")
    FUNCTION = "sample"
    CATEGORY = "🤖 GGUF-VLM/🚀 Business"

    def sample(self, video, max_frames=8, strategy="uniform"):
        frame_count = int(video.shape[0])
        indices = select_frame_indices(frame_count, max_frames, strategy)
        return (video[indices], ",".join(str(i) for i in indices))


class VLMModelAdvisor:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "task": (["caption/标注", "ocr/文字识别", "prompt reverse/反推", "json/结构化", "video/视频理解", "custom/自定义"], {"default": "caption/标注"}),
                "vram_gb": ("INT", {"default": 8, "min": 0, "max": 128, "step": 1}),
                "privacy": (["本地优先", "远程可用", "remote preferred"], {"default": "本地优先"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("recommendation",)
    FUNCTION = "advise"
    CATEGORY = "🤖 GGUF-VLM/🚀 Business"

    def advise(self, task="caption/标注", vram_gb=8, privacy="本地优先"):
        return (recommend_vlm_setup(task, vram_gb, privacy),)


class JSONResultValidator:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json_text": (IO.STRING, {"default": "{}", "multiline": True}),
                "required_fields": (IO.STRING, {"default": "subject,tags", "multiline": False}),
            }
        }

    RETURN_TYPES = ("BOOLEAN", "STRING", "STRING")
    RETURN_NAMES = ("valid", "normalized_json", "error")
    FUNCTION = "validate"
    CATEGORY = "🤖 GGUF-VLM/🚀 Business"

    def validate(self, json_text="{}", required_fields="subject,tags"):
        import json

        fields = [field.strip() for field in required_fields.split(",") if field.strip()]
        result = validate_json_fields(json_text, fields)
        normalized = json.dumps(result["data"], ensure_ascii=False, indent=2) if result["data"] is not None else ""
        return (bool(result["valid"]), normalized, result["error"])


class BatchRemoteVLMTask:
    """Run the same remote VLM prompt over an IMAGE batch."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_config": ("REMOTE_VISION_MODEL", {}),
                "task": (["Caption", "OCR", "Prompt Reverse", "JSON", "Custom"], {"default": "Caption"}),
                "max_items": ("INT", {"default": 16, "min": 1, "max": 256, "step": 1}),
                "max_tokens": ("INT", {"default": 1024, "min": 1, "max": 8192, "step": 1}),
                "temperature": ("FLOAT", {"default": 0.2, "min": 0.0, "max": 2.0, "step": 0.1}),
                "timeout": ("INT", {"default": 300, "min": 30, "max": 1800, "step": 30}),
            },
            "optional": {
                "images": ("IMAGE", {}),
                "custom_prompt": (IO.STRING, {"default": "", "multiline": True}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("results_json", "results_text")
    FUNCTION = "run_batch"
    CATEGORY = "🤖 GGUF-VLM/🚀 Business"
    OUTPUT_NODE = True

    def _prompt_for_task(self, task, custom_prompt):
        if custom_prompt and custom_prompt.strip():
            return custom_prompt.strip()
        runner = RemoteVLMTaskRunner()
        return runner._default_prompt(task)

    def run_batch(
        self,
        model_config,
        task="Caption",
        max_items=16,
        max_tokens=1024,
        temperature=0.2,
        timeout=300,
        images=None,
        custom_prompt="",
    ):
        import json

        if images is None:
            return ("[]", "")
        if not model_config.get("service_available", False):
            error = f"❌ 服务不可用: {model_config.get('base_url', 'unknown')}"
            return (json.dumps([{"label": "error", "error": error}], ensure_ascii=False, indent=2), error)

        count = min(int(images.shape[0]), int(max_items))
        labels = build_batch_labels(task.lower().replace(" ", "_"), count)
        prompt = self._prompt_for_task(task, custom_prompt)
        engine = get_unified_api_engine(model_config["base_url"], model_config["api_type"])
        backend = create_backend(model_config["api_type"], engine=engine)

        rows = []
        for idx in range(count):
            single = images[idx:idx + 1]
            try:
                result = backend.generate(
                    model=model_config.get("model_name", ""),
                    prompt=prompt,
                    image_urls=[image_to_data_url(single)],
                    system_prompt=model_config.get("system_prompt", ""),
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=timeout,
                )
                rows.append({"label": labels[idx], "index": idx, "result": result, "error": ""})
            except Exception as exc:
                rows.append({"label": labels[idx], "index": idx, "result": "", "error": str(exc)})

        results_json = json.dumps(rows, ensure_ascii=False, indent=2)
        results_text = "\n\n".join(f"[{row['label']}]\n{row['result'] or row['error']}" for row in rows)
        return (results_json, results_text)


class DynamicMultiImageCollector:
    """Collect up to 8 optional IMAGE inputs into one IMAGE batch."""

    @classmethod
    def INPUT_TYPES(cls):
        optional = {f"image_{idx}": ("IMAGE", {}) for idx in range(1, 9)}
        return {"required": {}, "optional": optional}

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "summary")
    FUNCTION = "collect"
    CATEGORY = "🤖 GGUF-VLM/🚀 Business"

    def collect(self, **kwargs):
        import torch

        images = [kwargs.get(f"image_{idx}") for idx in range(1, 9) if kwargs.get(f"image_{idx}") is not None]
        if not images:
            raise ValueError("At least one image input is required")
        batch = torch.cat(images, dim=0) if len(images) > 1 else images[0]
        return (batch, f"Collected {len(images)} image input(s), batch={int(batch.shape[0])}")


NODE_CLASS_MAPPINGS = {
    "CaptionPromptBuilder": CaptionPromptBuilder,
    "OCRPromptBuilder": OCRPromptBuilder,
    "PromptReverseBuilder": PromptReverseBuilder,
    "JSONPromptBuilder": JSONPromptBuilder,
    "RemoteVLMTaskRunner": RemoteVLMTaskRunner,
    "VideoFrameSampler": VideoFrameSampler,
    "VLMModelAdvisor": VLMModelAdvisor,
    "JSONResultValidator": JSONResultValidator,
    "BatchRemoteVLMTask": BatchRemoteVLMTask,
    "DynamicMultiImageCollector": DynamicMultiImageCollector,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CaptionPromptBuilder": "🏷️ Caption Prompt Builder",
    "OCRPromptBuilder": "🔤 OCR Prompt Builder",
    "PromptReverseBuilder": "🎨 Prompt Reverse Builder",
    "JSONPromptBuilder": "🧾 JSON Extraction Prompt Builder",
    "RemoteVLMTaskRunner": "🚀 Remote VLM Business Task",
    "VideoFrameSampler": "🎞️ Video Frame Sampler",
    "VLMModelAdvisor": "🧭 VLM Model Advisor",
    "JSONResultValidator": "✅ JSON Result Validator",
    "BatchRemoteVLMTask": "📦 Batch Remote VLM Task",
    "DynamicMultiImageCollector": "🧩 Dynamic Multi-Image Collector",
}


V3_NODE_METADATA = {
    "CaptionPromptBuilder": build_v3_node_metadata(
        "CaptionPromptBuilder",
        "Caption Prompt Builder",
        "GGUF-VLM/Business",
        {"style": "COMBO", "language": "COMBO", "domain": "STRING"},
        {"prompt": "STRING"},
        "Build reusable caption prompts for VLM workflows.",
    ),
    "RemoteVLMTaskRunner": build_v3_node_metadata(
        "RemoteVLMTaskRunner",
        "Remote VLM Business Task",
        "GGUF-VLM/Business",
        {"model_config": "REMOTE_VISION_MODEL", "image": "IMAGE", "custom_prompt": "STRING"},
        {"result": "STRING"},
        "Run caption, OCR, prompt reverse, JSON, or custom VLM tasks.",
    ),
    "VideoFrameSampler": build_v3_node_metadata(
        "VideoFrameSampler",
        "Video Frame Sampler",
        "GGUF-VLM/Business",
        {"video": "IMAGE", "max_frames": "INT", "strategy": "COMBO"},
        {"frames": "IMAGE", "indices": "STRING"},
        "Sample representative frames from an IMAGE batch.",
    ),
    "JSONResultValidator": build_v3_node_metadata(
        "JSONResultValidator",
        "JSON Result Validator",
        "GGUF-VLM/Business",
        {"json_text": "STRING", "required_fields": "STRING"},
        {"valid": "BOOLEAN", "normalized_json": "STRING", "error": "STRING"},
        "Validate top-level fields in VLM JSON output.",
    ),
    "BatchRemoteVLMTask": build_v3_node_metadata(
        "BatchRemoteVLMTask",
        "Batch Remote VLM Task",
        "GGUF-VLM/Business",
        {"model_config": "REMOTE_VISION_MODEL", "images": "IMAGE", "task": "COMBO"},
        {"results_json": "STRING", "results_text": "STRING"},
        "Run a remote VLM task over an IMAGE batch.",
    ),
    "DynamicMultiImageCollector": build_v3_node_metadata(
        "DynamicMultiImageCollector",
        "Dynamic Multi-Image Collector",
        "GGUF-VLM/Business",
        {f"image_{idx}": "IMAGE" for idx in range(1, 9)},
        {"images": "IMAGE", "summary": "STRING"},
        "Collect optional image inputs into a batch for VLM workflows.",
    ),
}
