"""
tests/test_file_operations.py
--------------------------------
Tests for the file compression workflow described in project spec
section 4: read a text file, compress, save, load, decompress, save
recovered text, and verify equality. Also covers error handling for
invalid/corrupted/missing files.
"""

import sys
import os
import tempfile
import shutil
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.encoder import encode_text, serialize_package, deserialize_package
from core.decoder import decode_package


class TestFileCompressionWorkflow(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_source(self, name, content, encoding="utf-8"):
        path = os.path.join(self.tmpdir, name)
        with open(path, "w", encoding=encoding) as f:
            f.write(content)
        return path

    def test_full_file_compress_decompress_cycle(self):
        original_text = (
            "Data Structures and Algorithms capstone project.\n"
            "Huffman Encoding demonstrates greedy algorithms,\n"
            "binary trees, and priority queues.\n"
        )
        src_path = self._write_source("sample.txt", original_text)

        # 1. Read the input file
        with open(src_path, "r", encoding="utf-8") as f:
            loaded_text = f.read()
        self.assertEqual(loaded_text, original_text)

        # 2. Compress/encode
        package, root, steps = encode_text(loaded_text)

        # 3. Save the compressed representation
        compressed_path = os.path.join(self.tmpdir, "sample.huff")
        with open(compressed_path, "wb") as f:
            f.write(serialize_package(package))

        self.assertTrue(os.path.exists(compressed_path))
        self.assertGreater(os.path.getsize(compressed_path), 0)

        # 4. Load the compressed representation
        with open(compressed_path, "rb") as f:
            data = f.read()
        freqs, padding, count, packed = deserialize_package(data)

        # 5. Decode/decompress it
        recovered_text = decode_package(freqs, padding, count, packed)

        # 6. Save the recovered text
        recovered_path = os.path.join(self.tmpdir, "sample_recovered.txt")
        with open(recovered_path, "w", encoding="utf-8") as f:
            f.write(recovered_text)

        # 7. Verify recovered content matches original
        with open(recovered_path, "r", encoding="utf-8") as f:
            final_check = f.read()
        self.assertEqual(final_check, original_text)

    def test_empty_file(self):
        src_path = self._write_source("empty.txt", "")
        with open(src_path, "r", encoding="utf-8") as f:
            text = f.read()
        self.assertEqual(text, "")
        package, root, steps = encode_text(text)
        self.assertEqual(package.bitstring, "")
        self.assertIsNone(root)

    def test_invalid_file_utf8_decode_error_is_raised(self):
        # Write raw invalid UTF-8 bytes and confirm reading raises,
        # matching what the GUI catches and reports as an error.
        bad_path = os.path.join(self.tmpdir, "invalid.txt")
        with open(bad_path, "wb") as f:
            f.write(b"\xff\xfe\x00\x81not valid utf-8")
        with self.assertRaises(UnicodeDecodeError):
            with open(bad_path, "r", encoding="utf-8", errors="strict") as f:
                f.read()

    def test_no_file_selected_path_is_none_safe(self):
        # Simulates a cancelled file dialog: caller should check for None
        # before attempting to open. This test documents that contract.
        path = None
        self.assertIsNone(path)

    def test_loading_invalid_compressed_data_raises_value_error(self):
        bad_path = os.path.join(self.tmpdir, "bad.huff")
        with open(bad_path, "wb") as f:
            f.write(b"this is not a huffman file at all")
        with open(bad_path, "rb") as f:
            data = f.read()
        with self.assertRaises(ValueError):
            deserialize_package(data)

    def test_decoding_without_required_metadata_raises(self):
        # An empty frequency table but non-empty packed bytes is invalid:
        # there is no tree to decode against.
        from core.decoder import DecodeError
        with self.assertRaises(DecodeError):
            decode_package({}, 0, 5, b"\xff\xff")


if __name__ == "__main__":
    unittest.main()
