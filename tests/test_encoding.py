"""
tests/test_encoding.py
------------------------
Tests for core/encoder.py: bitstring packing/unpacking, serialization
of the .huff container format, and basic encode correctness.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.encoder import (
    encode_text,
    _pack_bits,
    unpack_bits,
    serialize_package,
    deserialize_package,
    stored_file_size,
    MAGIC,
)


class TestBitPacking(unittest.TestCase):
    def test_pack_unpack_round_trip(self):
        for bits in ["", "1", "0", "101", "11111111", "1010101010101"]:
            packed, padding = _pack_bits(bits)
            recovered = unpack_bits(packed, padding)
            self.assertEqual(recovered, bits)

    def test_padding_is_within_valid_range(self):
        for length in range(0, 20):
            bits = "1" * length
            _, padding = _pack_bits(bits)
            self.assertGreaterEqual(padding, 0)
            self.assertLess(padding, 8)


class TestEncodeText(unittest.TestCase):
    def test_empty_text(self):
        package, root, steps = encode_text("")
        self.assertEqual(package.bitstring, "")
        self.assertIsNone(root)

    def test_single_char(self):
        package, root, steps = encode_text("aaaa")
        self.assertEqual(package.bitstring, "0000")

    def test_bit_length_matches_code_lengths(self):
        text = "aabbbcccc"
        package, root, steps = encode_text(text)
        expected_len = sum(len(package.codes[ch]) for ch in text)
        self.assertEqual(len(package.bitstring), expected_len)


class TestSerialization(unittest.TestCase):
    def test_serialize_deserialize_round_trip(self):
        text = "hello world, this is a test!"
        package, root, steps = encode_text(text)
        data = serialize_package(package)

        self.assertTrue(data.startswith(MAGIC))

        freqs, padding, count, packed = deserialize_package(data)
        self.assertEqual(freqs, package.frequencies)
        self.assertEqual(count, len(text))

    def test_stored_file_size_matches_actual_serialized_length(self):
        text = "aabbbcccc unicode test: caf\u00e9"
        package, root, steps = encode_text(text)
        computed = stored_file_size(package)
        actual = len(serialize_package(package))
        self.assertEqual(computed, actual)

    def test_deserialize_rejects_bad_magic(self):
        with self.assertRaises(ValueError):
            deserialize_package(b"NOTHUFF...")

    def test_deserialize_rejects_truncated_data(self):
        text = "some reasonably long test text for corruption testing"
        package, root, steps = encode_text(text)
        data = serialize_package(package)
        truncated = data[: len(data) // 2]
        with self.assertRaises(ValueError):
            deserialize_package(truncated)

    def test_deserialize_rejects_empty_bytes(self):
        with self.assertRaises(ValueError):
            deserialize_package(b"")


if __name__ == "__main__":
    unittest.main()
