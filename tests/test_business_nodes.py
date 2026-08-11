import importlib.util
import sys
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

sys.modules.setdefault("numpy", types.SimpleNamespace())

if "comfy" not in sys.modules:
    comfy = types.ModuleType("comfy")
    comfy_types = types.ModuleType("comfy.comfy_types")
    comfy_types.IO = types.SimpleNamespace(STRING="STRING")
    comfy.comfy_types = comfy_types
    sys.modules["comfy"] = comfy
    sys.modules["comfy.comfy_types"] = comfy_types


def load_module(name, rel_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class BusinessNodeTests(unittest.TestCase):
    def test_caption_prompt_includes_style_and_language(self):
        prompts = load_module("utils.business_prompts", "utils/business_prompts.py")

        prompt = prompts.build_caption_prompt("简洁", "中文", "商品图")

        self.assertIn("中文", prompt)
        self.assertIn("商品图", prompt)
        self.assertIn("简洁", prompt)

    def test_json_prompt_requests_valid_schema(self):
        prompts = load_module("utils.business_prompts", "utils/business_prompts.py")

        prompt = prompts.build_json_prompt("对象、动作、风格", "tags, subject, action")

        self.assertIn("valid JSON", prompt)
        self.assertIn("tags", prompt)
        self.assertIn("对象、动作、风格", prompt)

    def test_uniform_frame_indices_are_stable(self):
        video_utils = load_module("utils.video_utils", "utils/video_utils.py")

        self.assertEqual(video_utils.select_frame_indices(10, 4, "uniform"), [0, 3, 6, 9])
        self.assertEqual(video_utils.select_frame_indices(3, 8, "uniform"), [0, 1, 2])

    def test_openai_vision_message_places_text_before_images(self):
        backend = load_module("core.backends.vlm_backend", "core/backends/vlm_backend.py")

        messages = backend.build_openai_vision_messages(
            prompt="Describe",
            image_urls=["data:image/png;base64,AAA"],
            system_prompt="System",
        )

        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["content"][0]["type"], "text")
        self.assertEqual(messages[1]["content"][1]["type"], "image_url")

    def test_model_advisor_recommends_video_sampler_for_video_task(self):
        advisor = load_module("utils.model_advisor", "utils/model_advisor.py")

        result = advisor.recommend_vlm_setup("video/视频理解", 8, "本地优先")

        self.assertIn("Video Frame Sampler", result)
        self.assertIn("推荐后端", result)


if __name__ == "__main__":
    unittest.main()
