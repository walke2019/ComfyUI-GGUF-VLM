import json
import sys
import tempfile
import types
import unittest
import importlib.util
from pathlib import Path

sys.modules.setdefault("numpy", types.SimpleNamespace())
if "PIL" not in sys.modules:
    pil = types.ModuleType("PIL")
    image_mod = types.ModuleType("PIL.Image")
    image_mod.fromarray = lambda *args, **kwargs: types.SimpleNamespace(save=lambda *a, **k: None)
    pil.Image = image_mod
    sys.modules["PIL"] = pil
    sys.modules["PIL.Image"] = image_mod
sys.modules.setdefault("requests", types.SimpleNamespace())
if "comfy" not in sys.modules:
    comfy = types.ModuleType("comfy")
    comfy_types = types.ModuleType("comfy.comfy_types")
    comfy_types.IO = types.SimpleNamespace(STRING="STRING")
    comfy.comfy_types = comfy_types
    sys.modules["comfy"] = comfy
    sys.modules["comfy.comfy_types"] = comfy_types
sys.modules.setdefault("folder_paths", types.SimpleNamespace(temp_directory="tmp", models_dir="models", get_folder_paths=lambda name: []))


class V2Alpha7Tests(unittest.TestCase):
    def test_v2_node_mappings_include_replacement_targets(self):
        spec = importlib.util.spec_from_file_location("v2_nodes_under_test", Path("nodes/v2_nodes.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        NODE_CLASS_MAPPINGS = module.NODE_CLASS_MAPPINGS

        self.assertIn("V2RemoteVisionAnalysis", NODE_CLASS_MAPPINGS)
        self.assertIn("V2DynamicMultiImageAnalysis", NODE_CLASS_MAPPINGS)

    def test_workflow_migrator_rewrites_node_types(self):
        from utils.workflow_migrator import migrate_workflow_dict

        workflow = {"nodes": [{"id": 1, "type": "RemoteVisionAnalysis"}]}
        migrated = migrate_workflow_dict(workflow)

        self.assertEqual(migrated["nodes"][0]["type"], "V2RemoteVisionAnalysis")
        self.assertIn("v2_migration", migrated["extra"])

    def test_workflow_migrator_writes_file(self):
        from utils.workflow_migrator import migrate_workflow_file

        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "workflow.json"
            dst = Path(tmp) / "workflow.v2.json"
            src.write_text(json.dumps({"nodes": [{"type": "VisionLanguageNode"}]}), encoding="utf-8")

            migrate_workflow_file(src, dst)
            data = json.loads(dst.read_text(encoding="utf-8"))

        self.assertEqual(data["nodes"][0]["type"], "V2LocalVisionAnalysis")

    def test_dynamic_inputs_js_has_add_image_input_button(self):
        text = Path("web/dynamic_inputs.js").read_text(encoding="utf-8")

        self.assertIn("Add Image Input", text)
        self.assertIn("addInput", text)


if __name__ == "__main__":
    unittest.main()
