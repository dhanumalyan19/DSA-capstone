"""
gui/decompression_view.py
--------------------------
The "Decompress" tab. Two supported data sources:

  1. "Use Last Compressed Result" -- decode the package just produced on
     the Compress tab, entirely in memory (no file needed). This is what
     drives the automatic Lossless Verification against the original
     input text.

  2. "Load Compressed File..." -- open an actual .huff file from disk
     (which may have been produced in a previous session), decode it,
     and optionally save the recovered text. If the original text is
     not available (e.g. file loaded fresh, no in-memory original),
     verification is simply not claimed rather than faked.
"""

import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from core.encoder import deserialize_package
from core.decoder import decode_package, DecodeError
from gui import theme


class DecompressionView(ttk.Frame):
    def __init__(self, parent, state, on_pipeline_updated):
        super().__init__(parent, style="TFrame")
        self.state = state
        self.on_pipeline_updated = on_pipeline_updated
        self._original_for_verification = None
        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 12, "pady": 8}

        source_frame = ttk.Frame(self, style="Panel.TFrame")
        source_frame.pack(fill="x", **pad)

        ttk.Label(source_frame, text="1. Choose Compressed Data Source",
                  style="PanelHeading.TLabel").pack(anchor="w", padx=10, pady=(10, 6))

        btn_row = ttk.Frame(source_frame, style="Panel.TFrame")
        btn_row.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Button(btn_row, text="Use Last Compressed Result", style="Accent.TButton",
                   command=self._use_in_memory).pack(side="left")
        ttk.Button(btn_row, text="Load Compressed File (.huff)...",
                   command=self._load_file).pack(side="left", padx=(8, 0))

        self.source_label = ttk.Label(source_frame, text="No compressed data loaded.",
                                       style="PanelMuted.TLabel")
        self.source_label.pack(anchor="w", padx=10, pady=(0, 10))

        action_frame = ttk.Frame(self, style="Panel.TFrame")
        action_frame.pack(fill="x", **pad)

        ttk.Label(action_frame, text="2. Decode", style="PanelHeading.TLabel").pack(
            anchor="w", padx=10, pady=(10, 6)
        )
        action_row = ttk.Frame(action_frame, style="Panel.TFrame")
        action_row.pack(fill="x", padx=10, pady=(0, 10))

        self.btn_decode = ttk.Button(action_row, text="Decode", style="Accent.TButton",
                                      command=self._on_decode, state="disabled")
        self.btn_decode.pack(side="left")
        self.btn_save_recovered = ttk.Button(
            action_row, text="Save Recovered Text...", command=self._save_recovered,
            state="disabled",
        )
        self.btn_save_recovered.pack(side="left", padx=(8, 0))

        # Verification banner
        self.verify_var = tk.StringVar(value="")
        self.verify_label = ttk.Label(action_frame, textvariable=self.verify_var,
                                       style="Result.TLabel")
        self.verify_label.pack(anchor="w", padx=10, pady=(0, 10))

        result_frame = ttk.Frame(self, style="Panel.TFrame")
        result_frame.pack(fill="both", expand=True, **pad)
        ttk.Label(result_frame, text="3. Recovered Text", style="PanelHeading.TLabel").pack(
            anchor="w", padx=10, pady=(10, 6)
        )
        self.recovered_text = theme.styled_text_widget(result_frame, height=14, width=90)
        self.recovered_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.recovered_text.configure(state="disabled")

        self._pending_source = None  # ('memory',) or ('file', path)

    # ------------------------------------------------------------------
    def _use_in_memory(self):
        if self.state.package is None or self.state.package.bitstring is None:
            messagebox.showwarning(
                "Nothing to Decode",
                "No compressed result is available yet. Go to the Compress "
                "tab and run the pipeline (Analyze -> Build Tree -> Generate "
                "Codes -> Compress) first.",
            )
            return
        self._pending_source = ("memory",)
        self._original_for_verification = self.state.source_text
        self.source_label.configure(
            text="Source: in-memory result from the Compress tab "
                 f"({len(self.state.package.bitstring)} bits, "
                 f"{len(self.state.frequencies)} unique symbols)."
        )
        self.btn_decode.configure(state="normal")
        self.verify_var.set("")

    def _load_file(self):
        path = filedialog.askopenfilename(
            title="Load compressed file",
            filetypes=[("Huffman compressed file", "*.huff"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError as exc:
            messagebox.showerror("File Error", f"Could not open file:\n{exc}")
            return

        if not data:
            messagebox.showerror("Empty File", "The selected file is empty.")
            return

        try:
            frequencies, padding_bits, original_count, packed_bytes = deserialize_package(data)
        except ValueError as exc:
            messagebox.showerror("Invalid Compressed Data", str(exc))
            return

        self._pending_source = ("file", frequencies, padding_bits, original_count, packed_bytes)
        # Only claim verification if this file happens to match the text
        # currently loaded on the Compress tab; otherwise, no comparison.
        if (self.state.source_text and self.state.frequencies == frequencies):
            self._original_for_verification = self.state.source_text
        else:
            self._original_for_verification = None

        self.source_label.configure(
            text=f"Source: file '{path}' ({len(packed_bytes)} bytes payload, "
                 f"{len(frequencies)} unique symbols, {original_count} original symbols)."
        )
        self.btn_decode.configure(state="normal")
        self.verify_var.set("")

    # ------------------------------------------------------------------
    def _on_decode(self):
        if self._pending_source is None:
            return

        try:
            start = time.perf_counter()
            if self._pending_source[0] == "memory":
                pkg = self.state.package
                decoded = decode_package(
                    pkg.frequencies, pkg.padding_bits, pkg.original_symbol_count,
                    pkg.packed_bytes,
                )
            else:
                _, frequencies, padding_bits, original_count, packed_bytes = self._pending_source
                decoded = decode_package(frequencies, padding_bits, original_count, packed_bytes)
            elapsed = time.perf_counter() - start
        except DecodeError as exc:
            messagebox.showerror("Decode Error", f"Could not decode data:\n{exc}")
            return

        self.state.decoded_text = decoded
        self.state.decoding_seconds = elapsed

        self.recovered_text.configure(state="normal")
        self.recovered_text.delete("1.0", "end")
        self.recovered_text.insert("1.0", decoded)
        self.recovered_text.configure(state="disabled")
        self.btn_save_recovered.configure(state="normal")

        if self._original_for_verification is not None:
            passed = (decoded == self._original_for_verification)
            self.state.verification_result = passed
            if passed:
                self.verify_var.set("Lossless Verification: PASSED")
                self.verify_label.configure(style="Good.TLabel")
            else:
                self.verify_var.set("Lossless Verification: FAILED")
                self.verify_label.configure(style="Bad.TLabel")
        else:
            self.state.verification_result = None
            self.verify_var.set(
                "Lossless Verification: N/A (original text not available for comparison "
                f"-- decoded {len(decoded)} symbol(s) successfully in "
                f"{elapsed * 1000:.3f} ms)"
            )
            self.verify_label.configure(style="Result.TLabel")

        self.on_pipeline_updated()

    def _save_recovered(self):
        if self.state.decoded_text is None:
            return
        path = filedialog.asksaveasfilename(
            title="Save recovered text",
            defaultextension=".txt",
            filetypes=[("Text file", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.state.decoded_text)
        except OSError as exc:
            messagebox.showerror("Save Error", f"Could not save file:\n{exc}")
            return
        messagebox.showinfo("Saved", f"Recovered text saved to:\n{path}")

    def on_state_changed(self):
        pass
