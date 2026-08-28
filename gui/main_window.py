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
        self.geometry("1100x750")
        self.minsize(900, 600)

        theme.apply_theme(self)

        self.state_obj = AppState()

        self._build_header()
        self._build_tabs()

    def _build_header(self):
        header = ttk.Frame(self, style="TFrame")
        header.pack(fill="x", padx=20, pady=(16, 4))
        ttk.Label(header, text="Huffman Compression Studio", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header, text="Data Structures & Algorithms  --  Huffman Encoding",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(2, 0))

    def _build_tabs(self):
        notebook = ttk.Frame(self, style="TFrame")
        notebook.pack(fill="both", expand=True, padx=16, pady=12)

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

    def _on_pipeline_updated(self):
        """Called by CompressionView/DecompressionView after any real state
        change, so every other tab refreshes from the same shared state."""
        self.state_obj.notify()


def run():
    app = MainWindow()
    app.mainloop()
