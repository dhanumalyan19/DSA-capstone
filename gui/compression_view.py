"""
gui/compression_view.py
------------------------
The "Compress" tab. Lets the user type text or open a text file, then
walks through the real pipeline:

    Analyze (frequencies) -> Build Tree -> Generate Codes -> Compress -> Save

Each button genuinely calls into core/huffman.py, core/encoder.py -- there
is no fake/demo output. Buttons are disabled until their prerequisite
step has actually completed, which also visually teaches the required
order of operations.
"""

import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from core.huffman import calculate_frequencies, build_huffman_tree, generate_codes
from core.encoder import encode_text, serialize_package, stored_file_size
from gui import theme


class CompressionView(ttk.Frame):
    def __init__(self, parent, state, on_pipeline_updated):
        super().__init__(parent, style="TFrame")
        self.state = state
        self.on_pipeline_updated = on_pipeline_updated
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        pad = {"padx": 12, "pady": 8}

        # --- Input area -----------------------------------------------
        input_frame = ttk.Frame(self, style="Panel.TFrame")
        input_frame.pack(fill="both", expand=False, **pad)

        ttk.Label(input_frame, text="1. Input Text", style="PanelHeading.TLabel").pack(
            anchor="w", padx=10, pady=(10, 0)
        )
        ttk.Label(
            input_frame,
            text="Type text below, or open a text file. Then run the pipeline in order.",
            style="PanelMuted.TLabel",
        ).pack(anchor="w", padx=10, pady=(0, 6))

        self.text_widget = theme.styled_text_widget(input_frame, height=8, width=90)
        self.text_widget.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.text_widget.bind("<<Modified>>", self._on_text_modified)

        btn_row = ttk.Frame(input_frame, style="Panel.TFrame")
        btn_row.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Button(btn_row, text="Open Text File...", command=self._open_file).pack(side="left")
        ttk.Button(btn_row, text="Clear", command=self._clear_input).pack(side="left", padx=(8, 0))
        self.file_label = ttk.Label(btn_row, text="No file loaded", style="PanelMuted.TLabel")
        self.file_label.pack(side="left", padx=(12, 0))

        # --- Pipeline buttons -------------------------------------------
        pipeline_frame = ttk.Frame(self, style="Panel.TFrame")
        pipeline_frame.pack(fill="x", **pad)

        ttk.Label(pipeline_frame, text="2. Run the Pipeline", style="PanelHeading.TLabel").pack(
            anchor="w", padx=10, pady=(10, 6)
        )

        steps_row = ttk.Frame(pipeline_frame, style="Panel.TFrame")
        steps_row.pack(fill="x", padx=10, pady=(0, 10))

        self.btn_analyze = ttk.Button(steps_row, text="1. Analyze", style="Accent.TButton",
                                       command=self._on_analyze)
        self.btn_build = ttk.Button(steps_row, text="2. Build Tree", style="Accent.TButton",
                                     command=self._on_build_tree, state="disabled")
        self.btn_codes = ttk.Button(steps_row, text="3. Generate Codes", style="Accent.TButton",
                                     command=self._on_generate_codes, state="disabled")
        self.btn_compress = ttk.Button(steps_row, text="4. Compress", style="Accent.TButton",
                                        command=self._on_compress, state="disabled")
        self.btn_save = ttk.Button(steps_row, text="5. Save Compressed File...",
                                    command=self._on_save, state="disabled")

        for b in (self.btn_analyze, self.btn_build, self.btn_codes,
                  self.btn_compress, self.btn_save):
            b.pack(side="left", padx=(0, 8))

        # --- Status / results -------------------------------------------
        result_frame = ttk.Frame(self, style="Panel.TFrame")
        result_frame.pack(fill="both", expand=True, **pad)

        ttk.Label(result_frame, text="3. Result Summary", style="PanelHeading.TLabel").pack(
            anchor="w", padx=10, pady=(10, 6)
        )

        self.summary_text = theme.styled_text_widget(result_frame, height=12, width=90)
        self.summary_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.summary_text.configure(state="disabled")

    # ------------------------------------------------------------------
    def _set_summary(self, text):
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", text)
        self.summary_text.configure(state="disabled")

    def _on_text_modified(self, event=None):
        # tk.Text fires <<Modified>> repeatedly; reset the flag each time.
        self.text_widget.edit_modified(False)

    def _open_file(self):
        path = filedialog.askopenfilename(
            title="Open text file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8", errors="strict") as f:
                content = f.read()
        except UnicodeDecodeError:
            messagebox.showerror(
                "Invalid File",
                "This file is not valid UTF-8 text and cannot be loaded.",
            )
            return
        except OSError as exc:
            messagebox.showerror("File Error", f"Could not open file:\n{exc}")
            return

        self.text_widget.delete("1.0", "end")
        self.text_widget.insert("1.0", content)
        self.state.source_file_path = path
        self.file_label.configure(text=f"Loaded: {os.path.basename(path)}")
        self._reset_pipeline_buttons()

    def _clear_input(self):
        self.text_widget.delete("1.0", "end")
        self.state.source_file_path = None
        self.file_label.configure(text="No file loaded")
        self._reset_pipeline_buttons()
        self._set_summary("")

    def _reset_pipeline_buttons(self):
        self.btn_build.configure(state="disabled")
        self.btn_codes.configure(state="disabled")
        self.btn_compress.configure(state="disabled")
        self.btn_save.configure(state="disabled")

    def _current_text(self):
        return self.text_widget.get("1.0", "end-1c")

    # ------------------------------------------------------------------
    # Pipeline step 1: Analyze
    # ------------------------------------------------------------------
    def _on_analyze(self):
        text = self._current_text()
        if text == "":
            messagebox.showwarning("Empty Input", "Please enter text or open a file first.")
            return

        self.state.reset_compress_side()
        self.state.source_text = text
        self.state.frequencies = calculate_frequencies(text)

        total = len(text)
        unique = len(self.state.frequencies)
        top = list(self.state.frequencies.items())[:10]
        top_lines = "\n".join(f"    {sym!r:>8} : {freq}" for sym, freq in top)

        summary = (
            f"FREQUENCY ANALYSIS\n"
            f"{'-' * 50}\n"
            f"Total characters:     {total}\n"
            f"Distinct symbols:     {unique}\n\n"
            f"Top symbols by frequency:\n{top_lines}\n"
        )
        if unique > 10:
            summary += f"    ... and {unique - 10} more (see Code Table tab)\n"

        self._set_summary(summary)
        self.btn_build.configure(state="normal")
        self.btn_codes.configure(state="disabled")
        self.btn_compress.configure(state="disabled")
        self.btn_save.configure(state="disabled")
        self.on_pipeline_updated()

    # ------------------------------------------------------------------
    # Pipeline step 2: Build Tree (via the from-scratch MinHeap)
    # ------------------------------------------------------------------
    def _on_build_tree(self):
        root, steps = build_huffman_tree(self.state.frequencies)
        self.state.tree_root = root
        self.state.build_steps = steps

        summary = (
            "HUFFMAN TREE CONSTRUCTION (via MinHeap)\n"
            f"{'-' * 50}\n" + "\n".join(f"- {s}" for s in steps)
        )
        self._set_summary(summary)
        self.btn_codes.configure(state="normal")
        self.on_pipeline_updated()

    # ------------------------------------------------------------------
    # Pipeline step 3: Generate Codes
    # ------------------------------------------------------------------
    def _on_generate_codes(self):
        codes = generate_codes(self.state.tree_root)
        self.state.codes = codes

        total = sum(self.state.frequencies.values()) or 1
        lines = []
        for sym, freq in list(self.state.frequencies.items())[:15]:
            code = codes.get(sym, "")
            prob = freq / total
            lines.append(f"    {sym!r:>8}  freq={freq:<6} prob={prob:.4f}  code={code}")

        summary = (
            "HUFFMAN CODE GENERATION\n"
            f"{'-' * 50}\n"
            f"{len(codes)} prefix-free code(s) generated by recursive tree traversal:\n\n"
            + "\n".join(lines)
        )
        if len(codes) > 15:
            summary += f"\n    ... and {len(codes) - 15} more (see Code Table tab)"

        self._set_summary(summary)
        self.btn_compress.configure(state="normal")
        self.on_pipeline_updated()

    # ------------------------------------------------------------------
    # Pipeline step 4: Compress (encode)
    # ------------------------------------------------------------------
    def _on_compress(self):
        text = self.state.source_text
        start = time.perf_counter()
        package, root, steps = encode_text(text)
        elapsed = time.perf_counter() - start

        self.state.package = package
        self.state.encode_steps = steps
        self.state.encoding_seconds = elapsed

        original_bytes = len(text.encode("utf-8"))
        theoretical_bits = package.theoretical_bit_length
        stored_bytes = stored_file_size(package)

        preview_len = 120
        bit_preview = package.bitstring[:preview_len]
        if len(package.bitstring) > preview_len:
            bit_preview += " ... (truncated)"

        summary = (
            "ENCODING RESULT\n"
            f"{'-' * 50}\n"
            f"Original size:                 {original_bytes} bytes ({original_bytes * 8} bits)\n"
            f"Theoretical bitstream size:     {theoretical_bits} bits "
            f"({theoretical_bits / 8:.2f} bytes)\n"
            f"Actual stored .huff file size:  {stored_bytes} bytes "
            f"(includes frequency-table header needed for decoding)\n"
            f"Unique symbols:                 {len(self.state.frequencies)}\n"
            f"Encoding time:                  {elapsed * 1000:.3f} ms\n\n"
            f"Bitstream preview:\n{bit_preview}\n"
        )
        self._set_summary(summary)
        self.btn_save.configure(state="normal")
        self.on_pipeline_updated()

    # ------------------------------------------------------------------
    # Pipeline step 5: Save compressed file
    # ------------------------------------------------------------------
    def _on_save(self):
        path = filedialog.asksaveasfilename(
            title="Save compressed file",
            defaultextension=".huff",
            filetypes=[("Huffman compressed file", "*.huff"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            data = serialize_package(self.state.package)
            with open(path, "wb") as f:
                f.write(data)
        except OSError as exc:
            messagebox.showerror("Save Error", f"Could not save file:\n{exc}")
            return

        self.state.last_saved_compressed_path = path
        messagebox.showinfo("Saved", f"Compressed file saved to:\n{path}")

    # ------------------------------------------------------------------
    def on_state_changed(self):
        # Nothing external currently drives this view's own inputs; the
        # summary is refreshed by its own step handlers. Present for
        # interface consistency with other tabs.
        pass
