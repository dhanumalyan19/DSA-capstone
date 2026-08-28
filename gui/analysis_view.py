"""
gui/analysis_view.py
----------------------
The "Analysis" tab: the Compression Analysis Dashboard required by the
project spec, plus the entropy explanation and an optional comparison
against RLE / Shannon-Fano / LZW (Arithmetic Coding explicitly marked
as not implemented -- never faked).

All numbers come from core/metrics.py and core/comparison.py, computed
against whatever the Compress tab actually produced -- nothing here is
hard-coded.
"""

import tkinter as tk
from tkinter import ttk

from core.metrics import full_analysis, explain_entropy_gap
from core.comparison import compare_all
from gui import theme


class AnalysisView(ttk.Frame):
    def __init__(self, parent, state):
        super().__init__(parent, style="TFrame")
        self.state = state
        self._build_vars()
        self._build_ui()

    def _build_vars(self):
        self.original_size_var = tk.StringVar(value="-")
        self.stored_size_var = tk.StringVar(value="-")
        self.ratio_var = tk.StringVar(value="-")
        self.savings_var = tk.StringVar(value="-")

    def _build_ui(self):
        header = ttk.Frame(self, style="Panel.TFrame")
        header.pack(fill="x", padx=12, pady=(12, 6))
        ttk.Label(header, text="Compression Analysis Dashboard",
                  style="PanelHeading.TLabel").pack(anchor="w", padx=10, pady=(10, 4))
        ttk.Label(
            header,
            text="Live metrics from the most recent compression run.",
            style="PanelMuted.TLabel",
        ).pack(anchor="w", padx=10, pady=(0, 8))

        stats = ttk.Frame(header, style="Panel.TFrame")
        stats.pack(fill="x", padx=10, pady=(0, 12))
        for label, var in (
            ("Original", self.original_size_var),
            ("Stored", self.stored_size_var),
            ("Ratio", self.ratio_var),
            ("Savings", self.savings_var),
        ):
            card = theme.metric_card(stats, label, var)
            card.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_row = ttk.Frame(self, style="TFrame")
        btn_row.pack(fill="x", padx=12, pady=(0, 6))
        ttk.Button(btn_row, text="Run Comparison vs Other Techniques", style="Accent.TButton",
                   command=self._run_comparison).pack(anchor="w")

        body_frame = ttk.Frame(self, style="Panel.TFrame")
        body_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.metrics_text = theme.styled_text_widget(body_frame, height=28, width=100)
        self.metrics_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.metrics_text.configure(state="disabled")

    def _set_text(self, content):
        self.metrics_text.configure(state="normal")
        self.metrics_text.delete("1.0", "end")
        self.metrics_text.insert("1.0", content)
        self.metrics_text.configure(state="disabled")

    def on_state_changed(self):
        if not self.state.package or not self.state.frequencies:
            self.original_size_var.set("-")
            self.stored_size_var.set("-")
            self.ratio_var.set("-")
            self.savings_var.set("-")
            self._set_text(
                "Run the full pipeline on the Compress tab (Analyze -> Build Tree -> "
                "Generate Codes -> Compress) to populate the analysis dashboard."
            )
            return

        from core.encoder import stored_file_size
        pkg = self.state.package
        stored_bytes = stored_file_size(pkg)
        analysis = full_analysis(
            self.state.source_text, self.state.frequencies, self.state.codes,
            pkg.bitstring, stored_bytes,
            encoding_seconds=self.state.encoding_seconds,
            decoding_seconds=self.state.decoding_seconds,
        )
        explanation = explain_entropy_gap(analysis)
        self.original_size_var.set(f"{analysis['original_size_bytes']} bytes")
        self.stored_size_var.set(f"{analysis['stored_file_bytes']} bytes")
        self.ratio_var.set(f"{analysis['compression_ratio_stored']:.3f}:1")
        self.savings_var.set(f"{analysis['space_savings_stored_pct']:.2f}%")

        lines = []
        lines.append("SIZE METRICS")
        lines.append("-" * 60)
        lines.append(f"Original size:                {analysis['original_size_bytes']} bytes "
                      f"({analysis['original_size_bits']} bits)")
        lines.append(f"Unique symbols:                {analysis['unique_symbol_count']}")
        lines.append(f"Theoretical bitstream size:    {analysis['theoretical_bitstream_bits']} bits "
                      f"({analysis['theoretical_bitstream_bytes']:.2f} bytes)")
        lines.append(f"Actual stored file size:       {analysis['stored_file_bytes']} bytes "
                      f"({analysis['stored_file_bits']} bits) -- includes frequency-table header")
        lines.append("")
        lines.append("COMPRESSION RATIO  (Original / Compressed)")
        lines.append("-" * 60)
        lines.append(f"vs theoretical bitstream:      {analysis['compression_ratio_theoretical']:.3f} : 1")
        lines.append(f"vs actual stored file:         {analysis['compression_ratio_stored']:.3f} : 1")
        lines.append("")
        lines.append("SPACE SAVINGS %  ((Original - Compressed) / Original x 100)")
        lines.append("-" * 60)
        lines.append(f"vs theoretical bitstream:      {analysis['space_savings_theoretical_pct']:.2f} %")
        lines.append(f"vs actual stored file:         {analysis['space_savings_stored_pct']:.2f} %")
        lines.append("")
        lines.append("INFORMATION THEORY")
        lines.append("-" * 60)
        lines.append(f"Shannon entropy:               {analysis['entropy_bits_per_symbol']:.4f} bits/symbol")
        lines.append(f"Average Huffman code length:   {analysis['average_code_length_bits']:.4f} bits/symbol")
        lines.append(f"Gap (code length - entropy):   {analysis['entropy_vs_code_length_gap']:.4f} bits/symbol")
        lines.append("")
        lines.append(explanation)
        lines.append("")
        lines.append("TIMING")
        lines.append("-" * 60)
        enc = analysis["encoding_seconds"]
        dec = analysis["decoding_seconds"]
        lines.append(f"Encoding time:                 {enc * 1000:.3f} ms" if enc is not None else
                      "Encoding time:                 (not measured yet)")
        lines.append(f"Decoding time:                 {dec * 1000:.3f} ms" if dec is not None else
                      "Decoding time:                 (run Decode on the Decompress tab)")

        if self.state.verification_result is not None:
            lines.append("")
            lines.append(
                "Lossless Verification: PASSED"
                if self.state.verification_result else "Lossless Verification: FAILED"
            )

        self._set_text("\n".join(lines))

    def _run_comparison(self):
        if not self.state.frequencies:
            self._set_text("Run the pipeline on the Compress tab first.")
            return

        pkg = self.state.package
        huffman_bits = pkg.theoretical_bit_length if pkg else 0
        original_bits, rows = compare_all(self.state.source_text, self.state.frequencies, huffman_bits)

        lines = []
        lines.append("ALGORITHM COMPARISON  (same input, theoretical bitstream size)")
        lines.append("-" * 70)
        lines.append(f"Original size: {original_bits} bits\n")
        lines.append(f"{'Technique':<28}{'Bits':>10}{'Ratio':>10}{'Savings %':>14}")
        lines.append("-" * 70)
        for row in rows:
            if not row["implemented"]:
                lines.append(f"{row['technique']:<28}{'N/A':>10}{'N/A':>10}{'  (not implemented)':>14}")
                continue
            bits = row["bits"] if row["bits"] is not None else 0
            ratio = f"{row['ratio']:.3f}" if row["ratio"] else "N/A"
            savings = f"{row['savings_pct']:.2f}" if row["savings_pct"] is not None else "N/A"
            lines.append(f"{row['technique']:<28}{bits:>10}{ratio:>10}{savings:>14}")

        lines.append("")
        lines.append(
            "Notes: RLE, Shannon-Fano, and LZW are genuinely implemented in "
            "core/comparison.py and measured the same way. Arithmetic Coding "
            "is intentionally NOT implemented (would require big-integer/"
            "range-coder machinery beyond this capstone's scope) and is "
            "marked N/A rather than faked."
        )

        self._set_text("\n".join(lines))
