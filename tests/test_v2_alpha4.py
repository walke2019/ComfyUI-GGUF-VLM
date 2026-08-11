import unittest


class V2Alpha4Tests(unittest.TestCase):
    def test_sse_event_formats_text_delta(self):
        from utils.streaming import sse_event

        self.assertEqual(sse_event("hello"), "data: hello\n\n")

    def test_collect_openai_stream_chunks_extracts_content(self):
        from utils.streaming import collect_openai_stream_chunks

        chunks = [
            {"choices": [{"delta": {"content": "a"}}]},
            {"choices": [{"delta": {"content": "b"}}]},
            {"choices": [{"delta": {}}]},
        ]

        self.assertEqual(list(collect_openai_stream_chunks(chunks)), ["a", "b"])


if __name__ == "__main__":
    unittest.main()
