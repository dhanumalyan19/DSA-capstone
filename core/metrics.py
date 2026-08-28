"""
core/metrics.py
----------------
Compression analysis & information-theory calculations, all derived from
real, measured values -- never hard-coded or faked.

Formulas used:

    Shannon Entropy:
        H = -sum( p(x) * log2(p(x)) )  for each distinct symbol x

    Average Huffman Code Length:
        L = sum( p(x) * length(code(x)) )

    Compression Ratio:
        original_size_bits / compressed_size_bits
        (>1 means the compressed form is smaller)

    Space Savings %:
        ((original_size - compressed_size) / original_size) * 100
"""

import math


def calculate_entropy(frequencies):
    """
    Shannon entropy in bits/symbol: H = -sum(p * log2(p)).
    Returns 0.0 for empty input or a single-symbol input (which has
    zero uncertainty -- entropy is correctly zero in that case).
    """
    total = sum(frequencies.values())
    if total == 0:
        return 0.0

    entropy = 0.0
    for freq in frequencies.values():
        if freq == 0:
            continue
        p = freq / total
        entropy -= p * math.log2(p)
    return entropy


def average_code_length(frequencies, codes):
    """
    Weighted-average length (in bits) of the Huffman codes actually
    generated, weighted by each symbol's observed probability:
        L = sum(p(x) * len(code(x)))
    """
    total = sum(frequencies.values())
    if total == 0:
        return 0.0

    weighted_sum = 0.0
    for symbol, freq in frequencies.items():
        p = freq / total
        code_len = len(codes.get(symbol, ""))
        weighted_sum += p * code_len
    return weighted_sum


def compression_ratio(original_bits, compressed_bits):
    """original_size / compressed_size, guarding against division by zero."""
    if compressed_bits == 0:
        return 0.0
    return original_bits / compressed_bits


def space_savings_percent(original_bits, compressed_bits):
    """((original - compressed) / original) * 100, guarding against 0."""
    if original_bits == 0:
        return 0.0
    return ((original_bits - compressed_bits) / original_bits) * 100.0


def build_code_table_rows(frequencies, codes):
    """
    Build the rows for the GUI's Code Table view:
        Character | Frequency | Probability | Huffman Code | Code Length
    Sorted by frequency descending (most common symbols first).
    """
    total = sum(frequencies.values()) or 1
    rows = []
    for symbol, freq in frequencies.items():
        probability = freq / total
        code = codes.get(symbol, "")
        rows.append({
            "symbol": symbol,
            "frequency": freq,
            "probability": probability,
            "code": code,
            "code_length": len(code),
        })
    rows.sort(key=lambda r: (-r["frequency"], r["symbol"]))
    return rows


def full_analysis(text, frequencies, codes, bitstring, stored_bytes,
                   encoding_seconds=None, decoding_seconds=None):
    """
    Assemble the complete Analysis dashboard dictionary from real,
    already-computed values. `stored_bytes` is the actual serialized
    .huff file size (see core/encoder.stored_file_size), used to report
    the honest real-world compressed size including header overhead.
    """
    original_bits = len(text.encode("utf-8")) * 8
    theoretical_bits = len(bitstring)
    stored_bits = stored_bytes * 8

    entropy = calculate_entropy(frequencies)
    avg_len = average_code_length(frequencies, codes)

    result = {
        "original_symbol_count": len(text),
        "unique_symbol_count": len(frequencies),
        "original_size_bytes": len(text.encode("utf-8")),
        "original_size_bits": original_bits,
        "theoretical_bitstream_bits": theoretical_bits,
        "theoretical_bitstream_bytes": theoretical_bits / 8,
        "stored_file_bytes": stored_bytes,
        "stored_file_bits": stored_bits,
        "compression_ratio_theoretical": compression_ratio(original_bits, theoretical_bits),
        "compression_ratio_stored": compression_ratio(original_bits, stored_bits),
        "space_savings_theoretical_pct": space_savings_percent(original_bits, theoretical_bits),
        "space_savings_stored_pct": space_savings_percent(original_bits, stored_bits),
        "entropy_bits_per_symbol": entropy,
        "average_code_length_bits": avg_len,
        "entropy_vs_code_length_gap": avg_len - entropy,
        "encoding_seconds": encoding_seconds,
        "decoding_seconds": decoding_seconds,
    }
    return result


def explain_entropy_gap(analysis):
    """
    Generate a short, plain-English explanation from the ACTUAL computed
    entropy and average code length -- never a canned/generic string
    detached from the numbers.
    """
    entropy = analysis["entropy_bits_per_symbol"]
    avg_len = analysis["average_code_length_bits"]
    gap = analysis["entropy_vs_code_length_gap"]

    if analysis["unique_symbol_count"] <= 1:
        return (
            "Only one distinct symbol appears in the input, so its Shannon "
            "entropy is 0 bits/symbol (no uncertainty). Huffman still needs "
            "1 bit per occurrence to mark 'this symbol occurred', which is "
            "the minimum possible for a non-empty stream."
        )

    if gap < 0.001:
        closeness = "is essentially identical to"
    elif gap < 0.25:
        closeness = "is very close to"
    elif gap < 1.0:
        closeness = "is reasonably close to"
    else:
        closeness = "is noticeably higher than"

    return (
        f"The source entropy is {entropy:.4f} bits/symbol, and the average "
        f"Huffman code length achieved is {avg_len:.4f} bits/symbol. The "
        f"average code length {closeness} the theoretical entropy limit "
        f"(gap = {gap:.4f} bits/symbol), indicating "
        f"{'highly efficient' if gap < 0.25 else 'reasonably efficient' if gap < 1.0 else 'less efficient'} "
        "prefix coding for this particular input. Huffman coding is "
        "guaranteed to reach the entropy limit only when all symbol "
        "probabilities are exact powers of 1/2; real text rarely satisfies "
        "that, which is the source of any remaining gap."
    )
