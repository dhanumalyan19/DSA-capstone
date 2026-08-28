"""
core/encoder.py
----------------
Turns input text into an actual Huffman-encoded representation, and
defines the on-disk container format used when saving a ".huff" file.

Two sizes are tracked and reported honestly (see project spec section 5):

  * theoretical_bit_length -- length of the raw Huffman bitstream itself
    (sum over symbols of frequency * code_length). This is the number
    that textbook "compression ratio" examples usually quote.

  * stored_byte_size -- the size of the *actual file we would write to
    disk*, which must also include the frequency table (so the decoder
    can rebuild the same tree) plus a small fixed header. This is the
    honest, real-world compressed size.

Container format written by `serialize_package`:

    b"HUFF1"                      5  bytes  magic / version
    symbol_count                  4  bytes  unsigned int, big-endian
    for each symbol:
        symbol utf-8 length       1  byte
        symbol utf-8 bytes        variable
        frequency                 4  bytes  unsigned int, big-endian
    padding_bits                  1  byte   (0-7, padding added to last byte)
    original_symbol_count         4  bytes  unsigned int, big-endian
    packed bitstream              variable  (the actual compressed payload)
"""

import struct
from core.huffman import calculate_frequencies, build_huffman_tree, generate_codes

MAGIC = b"HUFF1"


class CompressedPackage:
    """In-memory representation of an encoded result, before/after file I/O."""

    def __init__(self, frequencies, codes, bitstring, original_symbol_count):
        self.frequencies = frequencies
        self.codes = codes
        self.bitstring = bitstring                        # str of '0'/'1'
        self.original_symbol_count = original_symbol_count

    @property
    def theoretical_bit_length(self):
        return len(self.bitstring)

    @property
    def packed_bytes(self):
        return _pack_bits(self.bitstring)[0]

    @property
    def padding_bits(self):
        return _pack_bits(self.bitstring)[1]


def _pack_bits(bitstring):
    """
    Pack a string of '0'/'1' characters into actual bytes.
    Returns (bytes_obj, padding_bits_added).

    Because file storage is byte-aligned, the bitstring is padded with
    trailing zero bits to reach a multiple of 8; the padding count is
    stored so the decoder can strip exactly that many bits back off.
    """
    if bitstring == "":
        return b"", 0

    padding = (8 - (len(bitstring) % 8)) % 8
    padded = bitstring + ("0" * padding)

    out = bytearray()
    for i in range(0, len(padded), 8):
        byte_chunk = padded[i:i + 8]
        out.append(int(byte_chunk, 2))
    return bytes(out), padding


def unpack_bits(data, padding_bits):
    """Inverse of _pack_bits: bytes -> original (unpadded) bit string."""
    if not data:
        return ""
    bits = "".join(f"{byte:08b}" for byte in data)
    if padding_bits:
        bits = bits[:-padding_bits]
    return bits


def encode_text(text):
    """
    Full encode pipeline for raw text:
        text -> frequencies -> tree -> codes -> bitstring -> CompressedPackage

    Returns (package, root, steps) where `root` is the Huffman tree (the
    caller typically already has this from the Compress tab, but it is
    returned here too for convenience/testing) and `steps` narrates the
    encoding stage specifically.
    """
    steps = []
    frequencies = calculate_frequencies(text)

    if not frequencies:
        empty_package = CompressedPackage({}, {}, "", 0)
        steps.append("Nothing to encode -- input was empty.")
        return empty_package, None, steps

    root, _ = build_huffman_tree(frequencies)
    codes = generate_codes(root)

    bits = []
    for ch in text:
        bits.append(codes[ch])
    bitstring = "".join(bits)

    steps.append(
        f"Encoding complete: {len(text)} input symbol(s) mapped through the "
        f"code table into a bitstream of {len(bitstring)} bits."
    )

    package = CompressedPackage(frequencies, codes, bitstring, len(text))
    return package, root, steps


def serialize_package(package):
    """Serialize a CompressedPackage into the actual bytes of a .huff file."""
    buf = bytearray()
    buf += MAGIC
    buf += struct.pack(">I", len(package.frequencies))

    for symbol, freq in package.frequencies.items():
        sym_bytes = symbol.encode("utf-8")
        if len(sym_bytes) > 255:
            raise ValueError("Symbol too large to serialize (utf-8 > 255 bytes)")
        buf += struct.pack(">B", len(sym_bytes))
        buf += sym_bytes
        buf += struct.pack(">I", freq)

    packed, padding = _pack_bits(package.bitstring)
    buf += struct.pack(">B", padding)
    buf += struct.pack(">I", package.original_symbol_count)
    buf += packed

    return bytes(buf)


def deserialize_package(data):
    """
    Parse the bytes of a .huff file back into (frequencies, padding_bits,
    original_symbol_count, packed_bytes). Raises ValueError on malformed
    or corrupted data, so callers can show a friendly error message
    instead of crashing.
    """
    if len(data) < len(MAGIC):
        raise ValueError("File is too small to be a valid .huff file.")

    if data[:len(MAGIC)] != MAGIC:
        raise ValueError(
            "Invalid file header -- this does not look like a .huff file "
            "produced by this application."
        )

    offset = len(MAGIC)
    try:
        (symbol_count,) = struct.unpack_from(">I", data, offset)
        offset += 4

        frequencies = {}
        for _ in range(symbol_count):
            (sym_len,) = struct.unpack_from(">B", data, offset)
            offset += 1
            sym_bytes = data[offset:offset + sym_len]
            offset += sym_len
            symbol = sym_bytes.decode("utf-8")
            (freq,) = struct.unpack_from(">I", data, offset)
            offset += 4
            frequencies[symbol] = freq

        (padding_bits,) = struct.unpack_from(">B", data, offset)
        offset += 1
        (original_symbol_count,) = struct.unpack_from(">I", data, offset)
        offset += 4

        packed_bytes = data[offset:]
    except (struct.error, UnicodeDecodeError, IndexError) as exc:
        raise ValueError(f"Corrupted or invalid compressed data: {exc}") from exc

    if padding_bits > 7:
        raise ValueError("Corrupted compressed data: invalid padding value.")

    return frequencies, padding_bits, original_symbol_count, packed_bytes


def stored_file_size(package):
    """
    Actual byte size of the file that would be written to disk for this
    package, i.e. len(serialize_package(package)). Exposed separately
    (without needing to serialize twice) for the Analysis dashboard.
    """
    header_size = len(MAGIC) + 4  # magic + symbol_count
    for symbol in package.frequencies:
        header_size += 1 + len(symbol.encode("utf-8")) + 4
    header_size += 1 + 4  # padding_bits + original_symbol_count
    packed, _ = _pack_bits(package.bitstring)
    return header_size + len(packed)
