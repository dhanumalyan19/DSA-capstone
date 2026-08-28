"""
core/node.py
------------
Defines the HuffmanNode class used to build the Huffman Tree.

Each node is either:
  - A LEAF node: holds a real symbol (character) and its frequency.
  - An INTERNAL node: holds the combined frequency of its two children
    and has no symbol of its own.

A total insertion order counter (`order`) is kept so that when two nodes
have equal frequency, the heap has a stable, deterministic tie-breaker.
This matters for reproducibility: the same input should always build the
exact same tree.
"""


class HuffmanNode:
    """A single node in the Huffman binary tree."""

    def __init__(self, symbol, frequency, left=None, right=None, order=0):
        self.symbol = symbol          # The character (None for internal nodes)
        self.frequency = frequency    # Frequency / weight of this (sub)tree
        self.left = left              # Left child (edge label '0')
        self.right = right            # Right child (edge label '1')
        self.order = order            # Insertion order, used as a tie-breaker

    def is_leaf(self):
        """A leaf node has no children -- it represents an actual symbol."""
        return self.left is None and self.right is None

    def __lt__(self, other):
        """
        Comparison operator required by the min-heap.

        Primary key: frequency (lower frequency = higher priority).
        Secondary key: insertion order (stable tie-break so that runs
        are deterministic and easy to reason about during a viva).
        """
        if self.frequency != other.frequency:
            return self.frequency < other.frequency
        return self.order < other.order

    def __repr__(self):
        sym = repr(self.symbol) if self.symbol is not None else "*"
        return f"HuffmanNode(symbol={sym}, freq={self.frequency})"
