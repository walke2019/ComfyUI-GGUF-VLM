import unittest


class FakeStreamingEngine:
    def chat_completion(self, **kwargs):
        if kwargs.get("stream"):
            return [
                {"choices": [{"delta": {"content": "he"}}]},
                {"choices": [{"delta": {"content": "llo"}}]},
            ]
        return {"choices": [{"message": {"content": "hello"}}]}


class V2Alpha3Tests(unittest.TestCase):
    def test_stream_text_collects_chunks(self):
        from core.backends.factory import create_backend

        backend = create_backend("OpenAI Compatible", engine=FakeStreamingEngine())

        chunks = list(backend.stream_generate(model="m", prompt="p"))

        self.assertEqual(chunks, ["he", "llo"])

    def test_catalog_advisor_uses_catalog_recommendations(self):
        from utils.model_advisor import recommend_vlm_setup

        result = recommend_vlm_setup("caption", 4, "本地优先")

        self.assertIn("smolvlm2", result.lower())
        self.assertIn("Model Catalog 2.0", result)

    def test_batch_prompt_names_include_index(self):
        from utils.batch_utils import build_batch_labels

        self.assertEqual(build_batch_labels("caption", 3), ["caption_0001", "caption_0002", "caption_0003"])


if __name__ == "__main__":
    unittest.main()
