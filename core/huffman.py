"""
core/huffman.py
----------------
The heart of the DSA project: frequency analysis, Huffman tree
construction using the from-scratch MinHeap, and recursive code
generation.

Pipeline implemented here:

    text  --(count symbols)-->  frequency table
    frequency table --(wrap in nodes, push to heap)--> min-heap
    min-heap --(extract-min twice, merge, repeat)--> Huffman Tree
    Huffman Tree --(recursive DFS)--> code table {symbol: '0101...'}

Every stage also appends a human-readable entry to a `steps` list so the
GUI's "Algorithm" tab can walk the user through exactly what happened,
using their own input data.
"""

from collections import Counter
from core.node import HuffmanNode
from core.heap import MinHeap


class HuffmanBuildResult:
    """Container bundling everything produced while building a Huffman tree."""

    def __init__(self, frequencies, root, codes, steps):
        self.frequencies = frequencies    # dict: symbol -> count
        self.root = root                  # HuffmanNode: tree root
        self.codes = codes                # dict: symbol -> '0'/'1' string
        self.steps = steps                # list[str]: narrated algorithm steps


def calculate_frequencies(text):
    """
    Count occurrences of every symbol (character) in `text`.

    Returns an ordered dict (symbol -> frequency), ordered by descending
    frequency for readable display purposes.

    Complexity: O(n) where n = len(text).
    """
    if text == "":
        return {}
    counts = Counter(text)
    # Sort by frequency desc, then by symbol for a stable, readable order.
    ordered = dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))
    return ordered


def build_huffman_tree(frequencies):
    """
    Build a Huffman tree from a {symbol: frequency} dict using the
    from-scratch MinHeap (core/heap.py), following the classic greedy
    algorithm:

        1. Create a leaf node for every symbol; push all into a min-heap.
        2. While more than one node remains in the heap:
             a. Pop the two lowest-frequency nodes (x, y).
             b. Merge them into a new internal node whose frequency is
                x.frequency + y.frequency, with x as left child (bit '0')
                and y as right child (bit '1').
             c. Push the merged node back into the heap.
        3. The single node left in the heap is the root of the tree.

    Special case: if there is exactly ONE distinct symbol, a Huffman code
    cannot legitimately be an empty string (every occurrence must still
    take at least 1 bit to encode/decode). We handle this by wrapping the
    single leaf under one synthetic internal root, giving that symbol the
    code '0'.

    Returns: (root_node, steps) where steps is a list of narration strings.

    Time complexity: O(n log n), where n = number of distinct symbols,
    because each of the ~n heap push/pop operations costs O(log n).
    """
    steps = []

    if not frequencies:
        steps.append("Input is empty -- there are no symbols to build a tree from.")
        return None, steps

    heap = MinHeap()
    order_counter = 0

    steps.append(
        f"Step 1: Created {len(frequencies)} leaf node(s), one per distinct "
        f"symbol, and pushed each into the min-heap (priority = frequency)."
    )

    for symbol, freq in frequencies.items():
        node = HuffmanNode(symbol=symbol, frequency=freq, order=order_counter)
        order_counter += 1
        heap.push(node)

    # --- Special case: only one distinct symbol in the whole input -------
    if len(heap) == 1:
        only_leaf = heap.pop_min()
        synthetic_root = HuffmanNode(
            symbol=None,
            frequency=only_leaf.frequency,
            left=only_leaf,
            right=None,
            order=order_counter,
        )
        steps.append(
            "Only one distinct symbol was found. A single leaf cannot receive "
            "an empty code, so a synthetic root was created with that leaf as "
            "its left child, giving the symbol the 1-bit code '0'."
        )
        return synthetic_root, steps

    merge_number = 1
    while len(heap) > 1:
        left = heap.pop_min()
        right = heap.pop_min()

        merged = HuffmanNode(
            symbol=None,
            frequency=left.frequency + right.frequency,
            left=left,
            right=right,
            order=order_counter,
        )
        order_counter += 1

        left_label = left.symbol if left.is_leaf() else "internal"
        right_label = right.symbol if right.is_leaf() else "internal"
        steps.append(
            f"Merge {merge_number}: Extracted two minimum-frequency nodes "
            f"({left_label!r} freq={left.frequency}) and "
            f"({right_label!r} freq={right.frequency}); merged into a new "
            f"internal node with frequency {merged.frequency}, then pushed "
            f"it back into the heap. Heap size is now {len(heap) + 1} before "
            f"the push, {len(heap)} nodes remain to process."
        )
        merge_number += 1

        heap.push(merged)

    root = heap.pop_min()
    steps.append(
        "Final step: exactly one node remains in the heap -- this is the "
        f"root of the completed Huffman Tree, with total frequency "
        f"{root.frequency} (equal to the total number of symbols processed)."
    )
    return root, steps


def generate_codes(root):
    """
    Recursively traverse the Huffman tree (DFS) to assign a binary code
    to every symbol: append '0' when moving to the left child, '1' when
    moving to the right child. A leaf's accumulated path is its code.

    Returns dict: symbol -> code string.

    Complexity: O(n) where n = number of nodes in the tree (visits each
    node exactly once).
    """
    codes = {}
    if root is None:
        return codes

    def _walk(node, path):
        if node is None:
            return
        if node.is_leaf():
            # Guarantee at least one bit even for the single-symbol case.
            codes[node.symbol] = path if path else "0"
            return
        _walk(node.left, path + "0")
        _walk(node.right, path + "1")

    _walk(root, "")
    return codes


def build_from_text(text):
    """
    Convenience one-shot pipeline: text -> frequencies -> tree -> codes.
    Returns a HuffmanBuildResult with everything the GUI needs, plus a
    combined narrated `steps` list covering frequency analysis and tree
    construction.
    """
    steps = []
    frequencies = calculate_frequencies(text)

    if not frequencies:
        steps.append("No input provided -- nothing to analyze.")
        return HuffmanBuildResult(frequencies, None, {}, steps)

    total = sum(frequencies.values())
    steps.append(
        f"Frequency analysis complete: {len(frequencies)} distinct symbol(s) "
        f"found across {total} total character(s)."
    )

    root, build_steps = build_huffman_tree(frequencies)
    steps.extend(build_steps)

    codes = generate_codes(root)
    steps.append(
        f"Code generation complete: {len(codes)} prefix-free binary code(s) "
        "assigned by recursively walking the tree (left = '0', right = '1')."
    )

    return HuffmanBuildResult(frequencies, root, codes, steps)


def tree_to_text_diagram(root, max_depth=None):
    """
    Render the Huffman tree as an indented text diagram, useful as a
    fallback/console view and for tests. The graphical tree view in the
    GUI (gui/tree_view.py) draws this same structure on a Canvas.
    """
    if root is None:
        return "(empty tree)"

    lines = []

    def _render(node, prefix, edge_label):
        if node is None:
            return
        if node.is_leaf():
            label = f"[{node.symbol!r}: {node.frequency}]"
        else:
            label = f"({node.frequency})"
        edge = f"{edge_label} " if edge_label else ""
        lines.append(f"{prefix}{edge}{label}")
        child_prefix = prefix + "    "
        _render(node.left, child_prefix, "0->")
        _render(node.right, child_prefix, "1->")

    _render(root, "", "")
    return "\n".join(lines)
