"""
tests/test_web_app.py
---------------------
Integration tests for the Flask web interface. These verify that the
browser-facing API uses the same core Huffman pipeline correctly.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from web.app import create_app


class TestWebApp(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_index_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Huffman Compression Studio", response.data)

    def test_compress_then_decompress_round_trip(self):
        text = "web huffman compression repeated repeated repeated"
        compressed = self.client.post("/api/compress", json={"text": text})
        self.assertEqual(compressed.status_code, 200)
        payload = compressed.get_json()

        self.assertTrue(payload["compressedBase64"])
        self.assertTrue(payload["tree"])
        self.assertEqual(payload["summary"]["characters"], len(text))
        self.assertGreater(len(payload["codeTable"]), 0)

        decompressed = self.client.post("/api/decompress", json={
            "compressedBase64": payload["compressedBase64"],
            "originalText": text,
        })
        self.assertEqual(decompressed.status_code, 200)
        decoded = decompressed.get_json()
        self.assertEqual(decoded["decodedText"], text)
        self.assertTrue(decoded["verification"])

    def test_sample_list_and_sample_load(self):
        sample_list = self.client.get("/api/samples")
        self.assertEqual(sample_list.status_code, 200)
        samples = sample_list.get_json()["samples"]
        self.assertGreaterEqual(len(samples), 5)

        sample = self.client.get("/api/samples/repetitive")
        self.assertEqual(sample.status_code, 200)
        payload = sample.get_json()
        self.assertEqual(payload["id"], "repetitive")
        self.assertIn("text", payload)
        self.assertGreater(len(payload["text"]), 0)

    def test_unknown_sample_is_rejected(self):
        response = self.client.get("/api/samples/not-a-sample")
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.get_json())

    def test_whitespace_only_text_is_valid_input(self):
        response = self.client.post("/api/compress", json={"text": "     "})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["summary"]["characters"], 5)
        self.assertEqual(payload["summary"]["uniqueSymbols"], 1)

    def test_empty_text_is_rejected(self):
        response = self.client.post("/api/compress", json={"text": ""})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_invalid_compressed_payload_is_rejected(self):
        response = self.client.post("/api/decompress", json={
            "compressedBase64": "not-valid-base64",
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())


if __name__ == "__main__":
    unittest.main()
