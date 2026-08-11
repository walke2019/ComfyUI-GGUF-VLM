import json
import unittest
from pathlib import Path


class V2Alpha6Tests(unittest.TestCase):
    def test_node_replacements_include_core_legacy_nodes(self):
        from utils.node_replacements import get_node_replacements

        replacements = get_node_replacements()

        self.assertEqual(replacements["VisionLanguageNode"], "V2LocalVisionAnalysis")
        self.assertEqual(replacements["RemoteVisionAnalysis"], "V2RemoteVisionAnalysis")

    def test_json_schema_validator_checks_nested_required_fields(self):
        from utils.json_schema_tools import validate_json_schema

        schema = {
            "required": ["subject", "meta"],
            "properties": {"meta": {"required": ["source"]}},
        }
        result = validate_json_schema('{"subject":"cat","meta":{}}', schema)

        self.assertFalse(result["valid"])
        self.assertIn("meta.source", result["missing_fields"])

    def test_batch_manifest_finds_image_files(self):
        from utils.batch_manifest import build_image_manifest

        manifest = build_image_manifest("workflows", extensions=[".png"])

        self.assertTrue(any(item["path"].endswith(".png") for item in manifest))

    def test_v2_example_workflow_exists_and_has_nodes(self):
        data = json.loads(Path("workflows/V2_Business_Example.json").read_text(encoding="utf-8"))

        self.assertIn("nodes", data)
        self.assertGreaterEqual(len(data["nodes"]), 3)

    def test_ci_workflow_runs_unittest(self):
        text = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")

        self.assertIn("python -m unittest", text)


if __name__ == "__main__":
    unittest.main()
