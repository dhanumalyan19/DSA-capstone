"""
gui/main_window.py
--------------------
Top-level application window: header, subtitle, and a ttk.Notebook
holding the six tabs described in the project spec (section 9):
Compress, Decompress, Huffman Tree, Code Table, Analysis, Algorithm.

This module only wires widgets together and owns the shared AppState;
it contains no Huffman/DSA logic itself (kept in core/), and no tab's
own widget logic (kept in its own gui/*_view.py module).
"""

import tkinter as tk
from tkinter import ttk

from gui.app_state import AppState
from gui import theme
from gui.compression_view import CompressionView
from gui.decompression_view import DecompressionView
from gui.tree_view import TreeView
from gui.code_table_view import CodeTableView
from gui.analysis_view import AnalysisView
from gui.algorithm_view import AlgorithmView


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Huffman Compression Studio")
        self.geometry("1180x780")
        self.minsize(960, 640)

        theme.apply_theme(self)

        self.state_obj = AppState()
        self._build_header_vars()

        self._build_header()
        self._build_tabs()
        self.on_state_changed()

    def _build_header_vars(self):
        self.source_status_var = tk.StringVar(value="No input")
        self.codes_status_var = tk.StringVar(value="0 codes")
        self.result_status_var = tk.StringVar(value="Not compressed")
        self.verify_status_var = tk.StringVar(value="Not decoded")

    def _build_header(self):
        header = ttk.Frame(self, style="TFrame")
        header.pack(fill="x", padx=22, pady=(18, 6))

        title_row = ttk.Frame(header, style="TFrame")
        title_row.pack(fill="x")

        title_block = ttk.Frame(title_row, style="TFrame")
        title_block.pack(side="left", fill="x", expand=True)
        ttk.Label(title_block, text="Huffman Compression Studio",
                  style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            title_block, text="Data Structures & Algorithms - Huffman Encoding",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        cards = ttk.Frame(header, style="TFrame")
        cards.pack(fill="x", pady=(16, 0))
        for label, var in (
            ("Source", self.source_status_var),
            ("Codes", self.codes_status_var),
            ("Compression", self.result_status_var),
            ("Verification", self.verify_status_var),
        ):
            card = theme.metric_card(cards, label, var)
            card.pack(side="left", fill="x", expand=True, padx=(0, 10))

    def _build_tabs(self):
        notebook = ttk.Frame(self, style="TFrame")
        notebook.pack(fill="both", expand=True, padx=18, pady=(8, 16))

        self.notebook = ttk.Notebook(notebook)
        self.notebook.pack(fill="both", expand=True)

        self.compression_view = CompressionView(
            self.notebook, self.state_obj, on_pipeline_updated=self._on_pipeline_updated
        )
        self.decompression_view = DecompressionView(
            self.notebook, self.state_obj, on_pipeline_updated=self._on_pipeline_updated
        )
        self.tree_view = TreeView(self.notebook, self.state_obj)
        self.code_table_view = CodeTableView(self.notebook, self.state_obj)
        self.analysis_view = AnalysisView(self.notebook, self.state_obj)
        self.algorithm_view = AlgorithmView(self.notebook, self.state_obj)

        self.notebook.add(self.compression_view, text="Compress")
        self.notebook.add(self.decompression_view, text="Decompress")
        self.notebook.add(self.tree_view, text="Huffman Tree")
        self.notebook.add(self.code_table_view, text="Code Table")
        self.notebook.add(self.analysis_view, text="Analysis")
        self.notebook.add(self.algorithm_view, text="Algorithm")

        for view in (self.compression_view, self.decompression_view, self.tree_view,
                     self.code_table_view, self.analysis_view, self.algorithm_view):
            self.state_obj.register(view)
        self.state_obj.register(self)

    def _on_pipeline_updated(self):
        """Called by CompressionView/DecompressionView after any real state
        change, so every other tab refreshes from the same shared state."""
        self.state_obj.notify()

    def on_state_changed(self):
        source_len = len(self.state_obj.source_text or "")
        unique_count = len(self.state_obj.frequencies or {})
        code_count = len(self.state_obj.codes or {})

        if source_len:
            self.source_status_var.set(f"{source_len} chars, {unique_count} unique")
        else:
            self.source_status_var.set("No input")

        self.codes_status_var.set(f"{code_count} code{'s' if code_count != 1 else ''}")

        if self.state_obj.package:
            bits = self.state_obj.package.theoretical_bit_length
            self.result_status_var.set(f"{bits} bits ready")
        else:
            self.result_status_var.set("Not compressed")

        if self.state_obj.verification_result is True:
            self.verify_status_var.set("Passed")
        elif self.state_obj.verification_result is False:
            self.verify_status_var.set("Failed")
        elif self.state_obj.decoded_text is not None:
            self.verify_status_var.set("Decoded")
        else:
            self.verify_status_var.set("Not decoded")


def run():
    app = MainWindow()
    app.mainloop()
