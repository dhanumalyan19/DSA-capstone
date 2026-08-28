"""
gui/code_table_view.py
------------------------
The "Code Table" tab: a sortable-looking ttk.Treeview listing every
symbol with its frequency, probability, and the actual Huffman code
assigned by the constructed tree (core/metrics.build_code_table_rows).
"""

import tkinter as tk
from tkinter import ttk

from core.metrics import build_code_table_rows
from gui import theme


class CodeTableView(ttk.Frame):
    def __init__(self, parent, state):
        super().__init__(parent, style="TFrame")
        self.state = state
        self.search_var = tk.StringVar(value="")
        self._rows = []
        self._build_ui()
        self.search_var.trace_add("write", lambda *_: self._apply_filter())

    def _build_ui(self):
        header = ttk.Frame(self, style="Panel.TFrame")
        header.pack(fill="x", padx=12, pady=(12, 6))
        ttk.Label(header, text="Huffman Code Table", style="PanelHeading.TLabel").pack(
            anchor="w", padx=10, pady=(10, 4)
        )
        tools = ttk.Frame(header, style="Panel.TFrame")
        tools.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Label(tools, text="Search", style="PanelMuted.TLabel").pack(side="left")
        self.search_entry = ttk.Entry(tools, textvariable=self.search_var, width=28)
        self.search_entry.pack(side="left", padx=(8, 0))

        self.info_label = ttk.Label(
            self, text="Run the pipeline on the Compress tab to populate this table.",
            style="Muted.TLabel",
        )
        self.info_label.pack(anchor="w", padx=16, pady=(0, 6))

        table_frame = ttk.Frame(self, style="Panel.TFrame")
        table_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        columns = ("symbol", "frequency", "probability", "code", "length")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)
        headings = {
            "symbol": "Character",
            "frequency": "Frequency",
            "probability": "Probability",
            "code": "Huffman Code",
            "length": "Code Length (bits)",
        }
        widths = {"symbol": 140, "frequency": 100, "probability": 130, "code": 220, "length": 140}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    def on_state_changed(self):
        self._rows = []

        if not self.state.frequencies:
            self.info_label.configure(
                text="Run the pipeline on the Compress tab to populate this table."
            )
            self._apply_filter()
            return

        self._rows = build_code_table_rows(self.state.frequencies, self.state.codes)
        self._apply_filter()

        self.info_label.configure(
            text=f"{len(self._rows)} distinct symbol(s). Table sorted by frequency (descending)."
        )

    def _apply_filter(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        needle = self.search_var.get().strip().lower()
        visible_count = 0
        for row in self._rows:
            display_symbol = _display_symbol(row["symbol"])
            code = row["code"] if row["code"] else "(not generated yet)"
            haystack = f"{display_symbol} {row['frequency']} {row['probability']:.4f} {code}".lower()
            if needle and needle not in haystack:
                continue
            self.tree.insert("", "end", values=(
                display_symbol,
                row["frequency"],
                f"{row['probability']:.4f}",
                code,
                row["code_length"] if row["code"] else "-",
            ))
            visible_count += 1

        if self._rows and needle:
            self.info_label.configure(
                text=f"Showing {visible_count} of {len(self._rows)} symbol(s)."
            )


def _display_symbol(symbol):
    special = {" ": "SPACE", "\n": "\\n (newline)", "\t": "\\t (tab)", "\r": "\\r"}
    if symbol in special:
        return special[symbol]
    if symbol.isprintable():
        return symbol
    return f"U+{ord(symbol):04X}"
