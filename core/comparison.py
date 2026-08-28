"""
core/comparison.py
-------------------
Optional comparison/benchmark module (project spec section 16).

Implements REAL, working versions of three additional techniques so
Huffman can be benchmarked against genuine alternatives on the same
input, all measured the same way (final compressed size in bits):

  * Run-Length Encoding (RLE)   -- fully implemented.
  * Shannon-Fano coding         -- fully implemented (a real, distinct
                                    prefix-code algorithm, top-down split
                                    by cumulative frequency, unlike
                                    Huffman's bottom-up merge).
  * LZW (Lempel-Ziv-Welch)      -- fully implemented, dictionary-based.

Arithmetic coding is NOT implemented (would require big-integer /
range-coder machinery that is out of scope for this capstone); it is
explicitly marked as NOT IMPLEMENTED rather than faked, per the
project's instruction not to populate charts with fake algorithms.
"""

import math


# ----------------------------------------------------------------------
# Run-Length Encoding
# ----------------------------------------------------------------------
def rle_encode_size_bits(text):
    """
    Real RLE: encode runs as (symbol, count) pairs. To keep the size
    estimate honest and comparable, each pair is costed as:
        8 bits for the symbol (assuming extended ASCII/byte symbols)
      + bits needed to store the run-length count (variable, using the
        minimum bits to represent the largest count seen, at least 1).
    Returns total encoded size in bits, or None if text is empty.
    """
    if text == "":
        return None

    runs = []
    prev = text[0]
    count = 1
    for ch in text[1:]:
        if ch == prev:
            count += 1
        else:
            runs.append((prev, count))
            prev = ch
            count = 1
    runs.append((prev, count))

    max_count = max(c for _, c in runs)
    count_bits = max(1, math.ceil(math.log2(max_count + 1)))
    symbol_bits = 8  # store each symbol as a byte, a common simple choice

    total_bits = len(runs) * (symbol_bits + count_bits)
    return total_bits


# ----------------------------------------------------------------------
# Shannon-Fano coding
# ----------------------------------------------------------------------
def _shannon_fano_recursive(symbols_with_freq, codes, prefix=""):
    """
    symbols_with_freq: list of (symbol, freq), already sorted descending
    by frequency for the current sublist.
    """
    if len(symbols_with_freq) == 1:
        symbol, _ = symbols_with_freq[0]
        codes[symbol] = prefix if prefix else "0"
        return

    total = sum(f for _, f in symbols_with_freq)
    running = 0
    split_index = 0
    best_diff = None

    # Find the split point that divides the list into two halves whose
    # frequency sums are as close to equal as possible.
    for i in range(len(symbols_with_freq)):
        running += symbols_with_freq[i][1]
        diff = abs((total - running) - running)
        if best_diff is None or diff < best_diff:
            best_diff = diff
            split_index = i

    left = symbols_with_freq[:split_index + 1]
    right = symbols_with_freq[split_index + 1:]

    if not right:
        # Degenerate split guard (can't split further); treat as leaves.
        for symbol, _ in left:
            codes[symbol] = prefix + "0" if prefix else "0"
        return

    _shannon_fano_recursive(left, codes, prefix + "0")
    _shannon_fano_recursive(right, codes, prefix + "1")


def shannon_fano_codes(frequencies):
    """
    Build Shannon-Fano codes from a {symbol: frequency} dict using the
    classic top-down, split-by-cumulative-frequency algorithm (distinct
    from Huffman's bottom-up greedy merge).
    Returns dict: symbol -> code string.
    """
    if not frequencies:
        return {}
    if len(frequencies) == 1:
        only_symbol = next(iter(frequencies))
        return {only_symbol: "0"}

    items = sorted(frequencies.items(), key=lambda kv: -kv[1])
    codes = {}
    _shannon_fano_recursive(items, codes)
    return codes


def shannon_fano_size_bits(text, frequencies):
    codes = shannon_fano_codes(frequencies)
    return sum(len(codes[ch]) for ch in text)


# ----------------------------------------------------------------------
# LZW (Lempel-Ziv-Welch)
# ----------------------------------------------------------------------
def lzw_encode(text):
    """
    Real LZW encoder over the input text. Returns a list of integer
    codes. Dictionary starts with all single characters seen (built
    dynamically, so it works for any Unicode input, not just ASCII).
    """
    if text == "":
        return [], 0

    # Seed the dictionary with every distinct character actually present.
    dictionary = {ch: i for i, ch in enumerate(sorted(set(text)))}
    next_code = len(dictionary)

    result = []
    current = ""
    for ch in text:
        combined = current + ch
        if combined in dictionary:
            current = combined
        else:
            result.append(dictionary[current])
            dictionary[combined] = next_code
            next_code += 1
            current = ch
    if current:
        result.append(dictionary[current])

    return result, next_code


def lzw_size_bits(text):
    """
    Estimate LZW compressed size honestly: each emitted code is stored
    using the minimum fixed bit-width capable of representing the
    largest code value produced (a common, simple, defensible costing
    scheme for a comparison chart).
    """
    codes, dictionary_final_size = lzw_encode(text)
    if not codes:
        return None
    max_code = max(codes)
    bits_per_code = max(1, math.ceil(math.log2(max_code + 1)))
    return len(codes) * bits_per_code


# ----------------------------------------------------------------------
# Aggregate comparison
# ----------------------------------------------------------------------
def compare_all(text, frequencies, huffman_bits):
    """
    Build a comparison table (list of dicts) across all implemented
    techniques plus Huffman's own already-computed size. Arithmetic
    coding is explicitly marked as not implemented rather than faked.
    """
    original_bits = len(text.encode("utf-8")) * 8 if text else 0

    rows = [
        {"technique": "Huffman Coding", "bits": huffman_bits, "implemented": True},
        {"technique": "Run-Length Encoding (RLE)", "bits": rle_encode_size_bits(text), "implemented": True},
        {"technique": "Shannon-Fano Coding", "bits": shannon_fano_size_bits(text, frequencies) if text else None, "implemented": True},
        {"technique": "LZW", "bits": lzw_size_bits(text), "implemented": True},
        {"technique": "Arithmetic Coding", "bits": None, "implemented": False},
    ]

    for row in rows:
        if row["bits"] and original_bits:
            row["ratio"] = original_bits / row["bits"]
            row["savings_pct"] = ((original_bits - row["bits"]) / original_bits) * 100.0
        else:
            row["ratio"] = None
            row["savings_pct"] = None

    return original_bits, rows
