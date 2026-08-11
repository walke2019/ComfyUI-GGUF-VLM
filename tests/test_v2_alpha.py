import unittest
import sys
import types
from pathlib import Path

sys.modules.setdefault("requests", types.SimpleNamespace())
sys.modules.setdefault("tqdm", types.SimpleNamespace(tqdm=lambda iterable=None, **kwargs: iterable))


class V2AlphaTests(unittest.TestCase):
    def test_v3_metadata_contains_stable_id_and_outputs(self):
        from utils.node_metadata import build_v3_node_metadata

        meta = build_v3_node_metadata(
            node_id="RemoteVLMTaskRunner",
            display_name="Remote VLM Business Task",
            category="GGUF-VLM/Business",
            inputs={"image": "IMAGE", "prompt": "STRING"},
            outputs={"result": "STRING"},
            description="Run business VLM tasks",
        )

        self.assertEqual(meta["schema_version"], 3)
        self.assertEqual(meta["id"], "RemoteVLMTaskRunner")
        self.assertEqual(meta["outputs"]["result"], "STRING")

    def test_backend_registry_includes_llamacpp_and_lmstudio(self):
        from core.backends.registry import get_backend_descriptors, normalize_backend_type

        descriptors = get_backend_descriptors()
        names = {item.key for item in descriptors}

        self.assertIn("llamacpp_server", names)
        self.assertIn("lmstudio", names)
        self.assertEqual(normalize_backend_type("LM Studio"), "lmstudio")
        self.assertEqual(normalize_backend_type("llama.cpp server"), "llamacpp_server")

    def test_model_catalog_recommends_low_vram_caption_model(self):
        from utils.model_catalog import load_model_catalog, recommend_models

        catalog = load_model_catalog(Path("model_catalog_v2.yaml"))
        recs = recommend_models(catalog, task="caption", max_vram_gb=8)
        ids = [item["id"] for item in recs]

        self.assertTrue("qwen3-vl-8b-gguf" in ids or "smolvlm2" in ids)

    def test_v2_migration_doc_has_required_sections(self):
        text = Path("docs/v2_migration.md").read_text(encoding="utf-8")

        self.assertIn("V3 Nodes", text)
        self.assertIn("Backend Adapter 2.0", text)
        self.assertIn("Model Catalog 2.0", text)
        self.assertIn("Compatibility", text)
