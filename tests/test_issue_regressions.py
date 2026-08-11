import importlib.util
import sys
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

if "numpy" not in sys.modules:
    sys.modules["numpy"] = types.SimpleNamespace()

if "folder_paths" not in sys.modules:
    sys.modules["folder_paths"] = types.SimpleNamespace(
        models_dir=str(ROOT / "test_models"),
        temp_directory=str(ROOT / "tmp"),
        get_folder_paths=lambda name: [],
    )

if "comfy" not in sys.modules:
    comfy = types.ModuleType("comfy")
    comfy_types = types.ModuleType("comfy.comfy_types")
    comfy_types.IO = types.SimpleNamespace(STRING="STRING")
    comfy.comfy_types = comfy_types
    sys.modules["comfy"] = comfy
    sys.modules["comfy.comfy_types"] = comfy_types

if "core.inference.unified_api_engine" not in sys.modules:
    inference_pkg = types.ModuleType("core.inference")
    unified_api = types.ModuleType("core.inference.unified_api_engine")
    unified_api.get_unified_api_engine = lambda *args, **kwargs: None
    sys.modules.setdefault("core.inference", inference_pkg)
    sys.modules["core.inference.unified_api_engine"] = unified_api

if "requests" not in sys.modules:
    sys.modules["requests"] = types.SimpleNamespace(get=lambda *args, **kwargs: None)


def load_module(name, rel_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class IssueRegressionTests(unittest.TestCase):
    def test_inference_engine_exposes_shared_global_instance(self):
        engine_mod = load_module("core.inference_engine", "core/inference_engine.py")

        first = engine_mod.get_global_inference_engine()
        second = engine_mod.get_global_inference_engine()

        self.assertIs(first, second)

    def test_windows_file_url_uses_valid_file_uri(self):
        path_utils = load_module("utils.path_utils", "utils/path_utils.py")

        self.assertEqual(
            path_utils.path_to_file_url(r"C:\tmp\image.png"),
            "file:///C:/tmp/image.png",
        )

    def test_mmproj_files_are_excluded_but_vl_models_remain_text_selectable(self):
        text_mod = load_module("nodes.unified_text_node", "nodes/unified_text_node.py")

        models = [
            "Qwen3-VL-8B-Instruct-Q4_K_M.gguf",
            "mmproj-Qwen3-VL-8B-Instruct-F16.gguf",
            "llama-3.1-8b-q4.gguf",
        ]

        filtered = text_mod.LocalTextModelLoader._filter_text_selectable_models(models)

        self.assertIn("Qwen3-VL-8B-Instruct-Q4_K_M.gguf", filtered)
        self.assertIn("llama-3.1-8b-q4.gguf", filtered)
        self.assertNotIn("mmproj-Qwen3-VL-8B-Instruct-F16.gguf", filtered)


if __name__ == "__main__":
    unittest.main()
