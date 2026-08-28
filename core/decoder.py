"""
core/decoder.py
----------------
Reconstructs the original text from a compressed package.

Design choice (deliberate, for DSA-teaching value): decoding is done by
walking the actual Huffman tree bit-by-bit (0 -> left, 1 -> right),
emitting a symbol every time a leaf is reached and resetting to the
root -- rather than by using a reversed code-to-symbol dictionary. This
mirrors exactly what a real decompressor does and is the version that
is easiest to explain during a viva ("we walk the tree; a leaf is a
finished symbol").
"""

from core.huffman import build_huffman_tree
from core.encoder import unpack_bits


class DecodeError(Exception):
    """Raised when a bitstream cannot be validly decoded against a tree."""


def decode_bits(root, bitstring, expected_symbol_count=None):
    """
    Walk `root` according to each bit in `bitstring`, emitting a symbol
    at every leaf. Returns the decoded string.

    Raises DecodeError if the bitstream is malformed (e.g. runs out of
    bits mid-path, meaning the data or tree is corrupted/mismatched).
    """
    if root is None:
        if bitstring == "":
            return ""
        raise DecodeError("No Huffman tree available to decode against.")

    # Special case: synthetic root with a single leaf child and no bits
    # consumed per symbol other than the fixed 1-bit code.
    decoded_chars = []
    node = root

    if root.is_leaf():
        # A tree that is just one leaf (shouldn't normally happen because
        # build_huffman_tree wraps single-symbol input in a synthetic
        # root, but handled defensively here too).
        count = expected_symbol_count if expected_symbol_count is not None else len(bitstring)
        return root.symbol * count

    for bit in bitstring:
        if bit == "0":
            node = node.left
        elif bit == "1":
            node = node.right
        else:
            raise DecodeError(f"Invalid bit encountered: {bit!r} (expected '0' or '1').")

        if node is None:
            raise DecodeError(
                "Bitstream took a path that does not exist in the Huffman "
                "tree -- the data is corrupted or does not match this tree."
            )

        if node.is_leaf():
            decoded_chars.append(node.symbol)
            node = root

    if node is not root:
        raise DecodeError(
            "Bitstream ended in the middle of a code -- the data is "
            "truncated or corrupted."
        )

    decoded_text = "".join(decoded_chars)

    if expected_symbol_count is not None and len(decoded_text) != expected_symbol_count:
        raise DecodeError(
            f"Decoded {len(decoded_text)} symbol(s) but expected "
            f"{expected_symbol_count}. Data may be corrupted."
        )

    return decoded_text


def decode_package(frequencies, padding_bits, original_symbol_count, packed_bytes):
    """
    Full decode pipeline used for both in-memory decode and file decode:
        frequencies -> rebuild tree -> unpack bytes to bits -> walk tree -> text

    This demonstrates that ONLY the frequency table (not the tree itself)
    needs to be stored -- the exact same greedy algorithm rebuilds an
    identical tree deterministically.
    """
    if not frequencies:
        if original_symbol_count:
            raise DecodeError(
                "Cannot decode: no frequency table (tree metadata) was "
                f"provided, but {original_symbol_count} symbol(s) were "
                "expected. The compressed data is missing required metadata."
            )
        return ""

    root, _ = build_huffman_tree(frequencies)
    bitstring = unpack_bits(packed_bytes, padding_bits)
    return decode_bits(root, bitstring, expected_symbol_count=original_symbol_count)
