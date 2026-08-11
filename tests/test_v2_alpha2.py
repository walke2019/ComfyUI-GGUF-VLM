import unittest


class FakeEngine:
    def __init__(self):
        self.called = False

    def is_service_available(self):
        return True

    def get_available_models(self, force_refresh=False):
        return ["model-a", "model-b"]

    def chat_completion(self, **kwargs):
        self.called = True
        return {"choices": [{"message": {"content": "ok"}}]}


class V2Alpha2Tests(unittest.TestCase):
    def test_backend_factory_creates_lmstudio_backend(self):
        from core.backends.factory import create_backend

        backend = create_backend("LM Studio", engine=FakeEngine())

        self.assertEqual(backend.key, "lmstudio")
        self.assertTrue(backend.health_check())
        self.assertEqual(backend.list_models(), ["model-a", "model-b"])
        self.assertEqual(backend.generate(model="model-a", prompt="hello"), "ok")

    def test_backend_factory_creates_llamacpp_server_backend(self):
        from core.backends.factory import create_backend

        backend = create_backend("llama.cpp server", engine=FakeEngine())

        self.assertEqual(backend.key, "llamacpp_server")
        self.assertTrue(backend.supports_video)

    def test_json_validator_accepts_required_fields(self):
        from utils.json_schema_tools import validate_json_fields

        result = validate_json_fields('{"subject":"cat","tags":["cute"]}', ["subject", "tags"])

        self.assertTrue(result["valid"])
        self.assertEqual(result["data"]["subject"], "cat")

    def test_json_validator_reports_missing_fields(self):
        from utils.json_schema_tools import validate_json_fields

        result = validate_json_fields('{"subject":"cat"}', ["subject", "tags"])

        self.assertFalse(result["valid"])
        self.assertIn("tags", result["missing_fields"])


if __name__ == "__main__":
    unittest.main()
