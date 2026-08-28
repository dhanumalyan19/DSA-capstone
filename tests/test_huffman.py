"""
tests/test_huffman.py
------------------------
Unit tests for frequency analysis, the from-scratch MinHeap, Huffman
tree construction, and code generation.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.heap import MinHeap
from core.node import HuffmanNode
from core.huffman import (
    calculate_frequencies,
    build_huffman_tree,
    generate_codes,
    build_from_text,
)


class TestMinHeap(unittest.TestCase):
    def test_pops_in_ascending_order(self):
        heap = MinHeap()
        values = [5, 3, 8, 1, 9, 2, 7]
        for i, v in enumerate(values):
            heap.push(HuffmanNode(symbol=str(v), frequency=v, order=i))

        popped = [heap.pop_min().frequency for _ in range(len(values))]
        self.assertEqual(popped, sorted(values))

    def test_len_and_is_empty(self):
        heap = MinHeap()
        self.assertTrue(heap.is_empty())
        heap.push(HuffmanNode("a", 1, order=0))
        self.assertEqual(len(heap), 1)
        self.assertFalse(heap.is_empty())
        heap.pop_min()
        self.assertTrue(heap.is_empty())

    def test_pop_empty_raises(self):
        heap = MinHeap()
        with self.assertRaises(IndexError):
            heap.pop_min()

    def test_peek_does_not_remove(self):
        heap = MinHeap()
        heap.push(HuffmanNode("a", 5, order=0))
        heap.push(HuffmanNode("b", 2, order=1))
        self.assertEqual(heap.peek().frequency, 2)
        self.assertEqual(len(heap), 2)

    def test_stable_tie_break_by_order(self):
        heap = MinHeap()
        heap.push(HuffmanNode("a", 5, order=1))
        heap.push(HuffmanNode("b", 5, order=0))
        first = heap.pop_min()
        self.assertEqual(first.symbol, "b")  # lower order wins the tie


class TestFrequencyAnalysis(unittest.TestCase):
    def test_empty_text(self):
        self.assertEqual(calculate_frequencies(""), {})

    def test_simple_counts(self):
        freqs = calculate_frequencies("aabbbcccc")
        self.assertEqual(freqs["a"], 2)
        self.assertEqual(freqs["b"], 3)
        self.assertEqual(freqs["c"], 4)

    def test_total_matches_length(self):
        text = "The quick brown fox jumps over the lazy dog."
        freqs = calculate_frequencies(text)
        self.assertEqual(sum(freqs.values()), len(text))


class TestTreeConstruction(unittest.TestCase):
    def test_empty_input_returns_none(self):
        root, steps = build_huffman_tree({})
        self.assertIsNone(root)
        self.assertTrue(len(steps) >= 1)

    def test_single_symbol_gets_code(self):
        freqs = calculate_frequencies("aaaa")
        root, _ = build_huffman_tree(freqs)
        codes = generate_codes(root)
        self.assertEqual(codes, {"a": "0"})

    def test_two_symbols_get_distinct_prefix_free_codes(self):
        freqs = calculate_frequencies("aaabb")
        root, _ = build_huffman_tree(freqs)
        codes = generate_codes(root)
        self.assertEqual(len(codes), 2)
        self.assertNotEqual(codes["a"], codes["b"])

    def test_codes_are_prefix_free(self):
        text = "this is a slightly longer test string for prefix testing"
        freqs = calculate_frequencies(text)
        root, _ = build_huffman_tree(freqs)
        codes = generate_codes(root)
        code_list = list(codes.values())
        for i, c1 in enumerate(code_list):
            for j, c2 in enumerate(code_list):
                if i == j:
                    continue
                self.assertFalse(
                    c2.startswith(c1),
                    f"Code {c1!r} is a prefix of {c2!r} -- violates prefix-free property",
                )

    def test_more_frequent_symbol_gets_shorter_or_equal_code(self):
        # 'c' is far more frequent than 'a' and 'b'; its code should not be longer.
        freqs = calculate_frequencies("a" * 1 + "b" * 1 + "c" * 50)
        root, _ = build_huffman_tree(freqs)
        codes = generate_codes(root)
        self.assertLessEqual(len(codes["c"]), len(codes["a"]))
        self.assertLessEqual(len(codes["c"]), len(codes["b"]))

    def test_build_from_text_bundles_everything(self):
        result = build_from_text("mississippi")
        self.assertEqual(sum(result.frequencies.values()), len("mississippi"))
        self.assertIsNotNone(result.root)
        self.assertEqual(len(result.codes), len(result.frequencies))
        self.assertTrue(len(result.steps) > 0)


if __name__ == "__main__":
    unittest.main()
