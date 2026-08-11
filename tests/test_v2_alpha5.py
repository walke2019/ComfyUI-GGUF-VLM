import unittest
from pathlib import Path


class V2Alpha5Tests(unittest.TestCase):
    def test_streaming_panel_has_visible_prompt_and_output_widgets(self):
        text = Path("web/streaming_panel.js").read_text(encoding="utf-8")

        self.assertIn("Streaming Prompt", text)
        self.assertIn("Streaming Output", text)
        self.assertIn("outputWidget.value", text)

    def test_streaming_panel_resizes_node_for_output(self):
        text = Path("web/streaming_panel.js").read_text(encoding="utf-8")

        self.assertIn("this.size", text)
        self.assertIn("setDirtyCanvas", text)


if __name__ == "__main__":
    unittest.main()
