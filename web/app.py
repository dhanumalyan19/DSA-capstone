"""
web/app.py
----------
Browser-based interface for the Huffman Compression Studio.

The web layer is intentionally thin: it accepts text or compressed bytes,
calls the existing core/ algorithms, and returns display-ready JSON for
the frontend. The DSA implementation remains in core/.
"""

import base64
import binascii
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from core.comparison import compare_all
from core.decoder import DecodeError, decode_package
from core.encoder import (
    deserialize_package,
    encode_text,
    serialize_package,
    stored_file_size,
)
from core.huffman import build_huffman_tree, calculate_frequencies, generate_codes
from core.metrics import build_code_table_rows, explain_entropy_gap, full_analysis

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = PROJECT_ROOT / "sample_data"
SAMPLE_FILES = {
    "normal": ("Normal English", "sample_normal.txt"),
    "repetitive": ("Highly Repetitive", "sample_repetitive.txt"),
    "source": ("Source Code", "sample_source_code.txt"),
    "random": ("Random Text", "sample_random.txt"),
    "small": ("Small Edge Case", "sample_small.txt"),
}


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/samples")
    def samples():
        return jsonify({
            "samples": [
                {"id": sample_id, "label": label}
                for sample_id, (label, _filename) in SAMPLE_FILES.items()
            ]
        })

    @app.get("/api/samples/<sample_id>")
    def sample(sample_id):
        if sample_id not in SAMPLE_FILES:
            return jsonify({"error": "Unknown sample."}), 404

        label, filename = SAMPLE_FILES[sample_id]
        path = SAMPLE_DIR / filename
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            return jsonify({"error": f"Could not load sample: {exc}"}), 500

        return jsonify({
            "id": sample_id,
            "label": label,
            "filename": filename,
            "text": text,
        })

    @app.post("/api/compress")
    def compress():
        payload = request.get_json(silent=True) or {}
        text = payload.get("text", "")
        if not isinstance(text, str):
            return jsonify({"error": "Input text must be a string."}), 400
        if text == "":
            return jsonify({"error": "Enter text before running compression."}), 400

        frequencies = calculate_frequencies(text)
        root, build_steps = build_huffman_tree(frequencies)
        codes = generate_codes(root)
        package, _encoded_root, encode_steps = encode_text(text)
        stored_bytes = stored_file_size(package)
        analysis = full_analysis(
            text,
            frequencies,
            codes,
            package.bitstring,
            stored_bytes,
        )
        entropy_explanation = explain_entropy_gap(analysis)
        original_bits, comparison_rows = compare_all(
            text, frequencies, package.theoretical_bit_length
        )
        compressed_bytes = serialize_package(package)

        steps = [
            f"Frequency analysis found {len(frequencies)} distinct symbol(s) "
            f"across {len(text)} total character(s).",
            *build_steps,
            f"Generated {len(codes)} prefix-free Huffman code(s).",
            *encode_steps,
        ]

        return jsonify({
            "summary": {
                "characters": len(text),
                "uniqueSymbols": len(frequencies),
                "originalBytes": analysis["original_size_bytes"],
                "theoreticalBits": package.theoretical_bit_length,
                "storedBytes": stored_bytes,
                "compressionRatio": analysis["compression_ratio_stored"],
                "spaceSavingsPct": analysis["space_savings_stored_pct"],
                "entropy": analysis["entropy_bits_per_symbol"],
                "averageCodeLength": analysis["average_code_length_bits"],
            },
            "frequencies": [
                {"symbol": _display_symbol(symbol), "rawSymbol": symbol, "frequency": freq}
                for symbol, freq in frequencies.items()
            ],
            "codes": {
                _display_symbol(symbol): code for symbol, code in codes.items()
            },
            "codeTable": [
                {
                    "symbol": _display_symbol(row["symbol"]),
                    "frequency": row["frequency"],
                    "probability": row["probability"],
                    "code": row["code"],
                    "codeLength": row["code_length"],
                }
                for row in build_code_table_rows(frequencies, codes)
            ],
            "tree": _tree_to_dict(root),
            "steps": steps,
            "bitPreview": _bit_preview(package.bitstring),
            "analysis": analysis,
            "entropyExplanation": entropy_explanation,
            "comparison": {
                "originalBits": original_bits,
                "rows": comparison_rows,
            },
            "compressedBase64": base64.b64encode(compressed_bytes).decode("ascii"),
            "compressedFileName": "compressed_output.huff",
        })

    @app.post("/api/decompress")
    def decompress():
        payload = request.get_json(silent=True) or {}
        encoded = payload.get("compressedBase64", "")
        original_text = payload.get("originalText")
        if not isinstance(encoded, str) or not encoded:
            return jsonify({"error": "No compressed data was provided."}), 400

        try:
            data = base64.b64decode(encoded, validate=True)
            frequencies, padding_bits, original_count, packed_bytes = deserialize_package(data)
            decoded = decode_package(frequencies, padding_bits, original_count, packed_bytes)
        except (binascii.Error, ValueError, DecodeError) as exc:
            return jsonify({"error": str(exc)}), 400

        verification = None
        if isinstance(original_text, str) and original_text != "":
            verification = decoded == original_text

        return jsonify({
            "decodedText": decoded,
            "characters": len(decoded),
            "uniqueSymbols": len(frequencies),
            "payloadBytes": len(packed_bytes),
            "verification": verification,
        })

    return app


def _tree_to_dict(node, bit=""):
    if node is None:
        return None

    data = {
        "symbol": _display_symbol(node.symbol) if node.symbol is not None else None,
        "frequency": node.frequency,
        "bit": bit,
        "leaf": node.is_leaf(),
        "children": [],
    }
    if node.left is not None:
        data["children"].append(_tree_to_dict(node.left, "0"))
    if node.right is not None:
        data["children"].append(_tree_to_dict(node.right, "1"))
    return data


def _display_symbol(symbol):
    if symbol is None:
        return "*"
    special = {
        " ": "SPACE",
        "\n": "\\n",
        "\t": "\\t",
        "\r": "\\r",
    }
    if symbol in special:
        return special[symbol]
    if symbol.isprintable():
        return symbol
    return f"U+{ord(symbol):04X}"


def _bit_preview(bitstring, limit=360):
    if len(bitstring) <= limit:
        return bitstring
    return f"{bitstring[:limit]}..."


def run(host="127.0.0.1", port=5000, debug=False):
    app = create_app()
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run(debug=True)
