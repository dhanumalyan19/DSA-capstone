"""
tests/test_metrics.py
------------------------
Tests for entropy, average code length, compression ratio, and space
savings calculations.
"""

import sys
import os
import math
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.huffman import calculate_frequencies, build_huffman_tree, generate_codes
from core.metrics import (
    calculate_entropy,
    average_code_length,
    compression_ratio,
    space_savings_percent,
    full_analysis,
    explain_entropy_gap,
)


class TestEntropy(unittest.TestCase):
    def test_empty_is_zero(self):
        self.assertEqual(calculate_entropy({}), 0.0)

    def test_single_symbol_is_zero(self):
        freqs = calculate_frequencies("aaaa")
        self.assertEqual(calculate_entropy(freqs), 0.0)

    def test_uniform_two_symbols_is_one_bit(self):
        freqs = {"a": 50, "b": 50}
        self.assertAlmostEqual(calculate_entropy(freqs), 1.0, places=6)

    def test_uniform_four_symbols_is_two_bits(self):
        freqs = {"a": 25, "b": 25, "c": 25, "d": 25}
        self.assertAlmostEqual(calculate_entropy(freqs), 2.0, places=6)

    def test_matches_manual_formula(self):
        freqs = {"a": 1, "b": 3}
        total = 4
        expected = -sum((f / total) * math.log2(f / total) for f in freqs.values())
        self.assertAlmostEqual(calculate_entropy(freqs), expected, places=9)


class TestAverageCodeLength(unittest.TestCase):
    def test_single_symbol_length_is_one(self):
        freqs = calculate_frequencies("aaaa")
        root, _ = build_huffman_tree(freqs)
        codes = generate_codes(root)
        self.assertEqual(average_code_length(freqs, codes), 1.0)

    def test_average_is_between_zero_and_max_code_length(self):
        text = "the quick brown fox jumps over the lazy dog"
        freqs = calculate_frequencies(text)
        root, _ = build_huffman_tree(freqs)
        codes = generate_codes(root)
        avg = average_code_length(freqs, codes)
        max_len = max(len(c) for c in codes.values())
        self.assertGreater(avg, 0)
        self.assertLessEqual(avg, max_len)

    def test_average_code_length_never_below_entropy_by_much(self):
        # Huffman's average code length is always >= entropy (Shannon's
        # source coding theorem) and typically within 1 bit of it.
        text = "mississippi river banks and mississippi mud"
        freqs = calculate_frequencies(text)
        root, _ = build_huffman_tree(freqs)
        codes = generate_codes(root)
        avg = average_code_length(freqs, codes)
        entropy = calculate_entropy(freqs)
        self.assertGreaterEqual(avg, entropy - 1e-9)
        self.assertLess(avg - entropy, 1.0)


class TestRatiosAndSavings(unittest.TestCase):
    def test_compression_ratio_basic(self):
        self.assertEqual(compression_ratio(800, 400), 2.0)

    def test_compression_ratio_zero_compressed_guarded(self):
        self.assertEqual(compression_ratio(800, 0), 0.0)

    def test_space_savings_basic(self):
        self.assertAlmostEqual(space_savings_percent(800, 400), 50.0)

    def test_space_savings_zero_original_guarded(self):
        self.assertEqual(space_savings_percent(0, 0), 0.0)


class TestFullAnalysis(unittest.TestCase):
    def test_full_analysis_runs_and_has_expected_keys(self):
        text = "aabbbcccc"
        freqs = calculate_frequencies(text)
        root, _ = build_huffman_tree(freqs)
        codes = generate_codes(root)
        bitstring = "".join(codes[ch] for ch in text)
        analysis = full_analysis(text, freqs, codes, bitstring, stored_bytes=50)

        for key in (
            "original_size_bytes", "theoretical_bitstream_bits", "stored_file_bytes",
            "compression_ratio_theoretical", "space_savings_theoretical_pct",
            "entropy_bits_per_symbol", "average_code_length_bits",
        ):
            self.assertIn(key, analysis)

    def test_explanation_mentions_single_symbol_case(self):
        text = "aaaa"
        freqs = calculate_frequencies(text)
        root, _ = build_huffman_tree(freqs)
        codes = generate_codes(root)
        bitstring = "".join(codes[ch] for ch in text)
        analysis = full_analysis(text, freqs, codes, bitstring, stored_bytes=20)
        explanation = explain_entropy_gap(analysis)
        self.assertIn("one distinct symbol", explanation)


if __name__ == "__main__":
    unittest.main()
