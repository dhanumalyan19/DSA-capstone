"""
tests/test_decoding.py
------------------------
Round-trip (encode -> serialize -> deserialize -> decode) correctness
tests, including the full set of edge cases called out in the project
spec section 10.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.encoder import encode_text, serialize_package, deserialize_package
from core.decoder import decode_package, decode_bits, DecodeError
from core.huffman import build_huffman_tree, calculate_frequencies


def round_trip(text):
    package, root, steps = encode_text(text)
    data = serialize_package(package)
    freqs, padding, count, packed = deserialize_package(data)
    return decode_package(freqs, padding, count, packed)


class TestRoundTripEdgeCases(unittest.TestCase):
    def test_empty_input(self):
        self.assertEqual(round_trip(""), "")

    def test_one_unique_character(self):
        self.assertEqual(round_trip("aaaaaaaaaa"), "aaaaaaaaaa")

    def test_two_unique_characters(self):
        self.assertEqual(round_trip("ababababab"), "ababababab")

    def test_normal_english_text(self):
        text = "The quick brown fox jumps over the lazy dog."
        self.assertEqual(round_trip(text), text)

    def test_text_with_spaces(self):
        text = "a b c   d     e"
        self.assertEqual(round_trip(text), text)

    def test_newlines(self):
        text = "line one\nline two\nline three\n"
        self.assertEqual(round_trip(text), text)

    def test_punctuation(self):
        text = "Hello, world! How are you? I'm fine; thanks... (really)"
        self.assertEqual(round_trip(text), text)

    def test_numbers(self):
        text = "0123456789 42 3.14159 -7"
        self.assertEqual(round_trip(text), text)

    def test_special_characters(self):
        text = "!@#$%^&*()_+-=[]{}|;':\",./<>?`~"
        self.assertEqual(round_trip(text), text)

    def test_unicode_characters(self):
        text = "caf\u00e9 na\u00efve r\u00e9sum\u00e9 \u4f60\u597d \U0001F600"
        self.assertEqual(round_trip(text), text)

    def test_very_small_input(self):
        self.assertEqual(round_trip("x"), "x")

    def test_larger_text(self):
        text = ("The quick brown fox jumps over the lazy dog. " * 200)
        self.assertEqual(round_trip(text), text)

    def test_highly_repetitive_text(self):
        text = "a" * 5000
        self.assertEqual(round_trip(text), text)

    def test_many_different_symbols(self):
        text = "".join(chr(c) for c in range(32, 127)) * 3
        self.assertEqual(round_trip(text), text)


class TestDecodeErrorHandling(unittest.TestCase):
    def test_decode_with_no_tree_and_nonempty_bits_raises(self):
        with self.assertRaises(DecodeError):
            decode_bits(None, "101")

    def test_decode_invalid_bit_character_raises(self):
        freqs = calculate_frequencies("aabbcc")
        root, _ = build_huffman_tree(freqs)
        with self.assertRaises(DecodeError):
            decode_bits(root, "012")

    def test_decode_truncated_bitstream_raises(self):
        freqs = calculate_frequencies("aabbbcccc")
        root, _ = build_huffman_tree(freqs)
        from core.huffman import generate_codes
        codes = generate_codes(root)
        # Take a valid code for 'a' or 'b' etc. and chop off its last bit
        full_code = next(c for c in codes.values() if len(c) > 1)
        truncated = full_code[:-1]
        with self.assertRaises(DecodeError):
            decode_bits(root, truncated)

    def test_deserialize_then_decode_on_corrupted_payload_raises_or_mismatches(self):
        package, root, steps = encode_text("aaabbbccc")
        data = bytearray(serialize_package(package))
        # Flip a byte inside the packed payload region (near the end).
        if len(data) > 0:
            data[-1] ^= 0xFF
        freqs, padding, count, packed = deserialize_package(bytes(data))
        # Either it raises DecodeError, or (rare) decodes to something that
        # no longer matches the original -- both are acceptable outcomes
        # for corrupted data, but it must never silently "succeed" with
        # the original text intact by coincidence in this test's design.
        try:
            decoded = decode_package(freqs, padding, count, packed)
            self.assertNotEqual(decoded, "aaabbbccc")
        except DecodeError:
            pass  # expected outcome


if __name__ == "__main__":
    unittest.main()
