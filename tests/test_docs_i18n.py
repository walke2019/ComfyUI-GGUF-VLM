import ast
import json
import re
import unittest
from pathlib import Path


class DocsI18nTests(unittest.TestCase):
    def test_readme_is_project_doc_not_long_roadmap_dump(self):
        text = Path("README.md").read_text(encoding="utf-8")

        self.assertIn("## Installation", text)
        self.assertIn("## 安装", text)
        self.assertIn("## Nodes", text)
        self.assertLess(len(text.splitlines()), 260)
        self.assertNotIn("v2.0-alpha.1", text)
        self.assertNotIn("Business Goals", text)

    def test_comfyui_i18n_node_defs_exist_for_en_and_zh(self):
        for lang in ("en", "zh"):
            path = Path("locales") / lang / "nodeDefs.json"
            self.assertTrue(path.exists(), f"missing {path}")
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("RemoteVLMTaskRunner", data)
            self.assertIn("display_name", data["RemoteVLMTaskRunner"])
            self.assertIn("inputs", data["RemoteVLMTaskRunner"])
            self.assertIn("outputs", data["RemoteVLMTaskRunner"])

    def test_i18n_covers_core_business_nodes(self):
        data = json.loads(Path("locales/en/nodeDefs.json").read_text(encoding="utf-8"))
        required = {
            "RemoteVLMTaskRunner",
            "BatchRemoteVLMTask",
            "JSONResultValidator",
            "DynamicMultiImageCollector",
            "VLMModelAdvisor",
        }

        self.assertTrue(required.issubset(set(data.keys())))

    def test_i18n_covers_registered_display_nodes(self):
        registered = set()
        for node_file in Path("nodes").glob("*.py"):
            text = node_file.read_text(encoding="utf-8")
            match = re.search(r"NODE_DISPLAY_NAME_MAPPINGS\s*=\s*(\{.*?\})", text, re.S)
            if match:
                registered.update(ast.literal_eval(match.group(1)).keys())

        for lang in ("en", "zh"):
            data = json.loads((Path("locales") / lang / "nodeDefs.json").read_text(encoding="utf-8"))
            missing = sorted(registered - set(data.keys()))
            self.assertEqual([], missing, f"missing {lang} i18n entries: {missing}")

    def test_i18n_main_files_exist_for_en_and_zh(self):
        for lang in ("en", "zh"):
            path = Path("locales") / lang / "main.json"
            self.assertTrue(path.exists(), f"missing {path}")
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("settingsCategories", data)


if __name__ == "__main__":
    unittest.main()
