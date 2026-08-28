"""
gui/code_table_view.py
------------------------
The "Code Table" tab: a sortable-looking ttk.Treeview listing every
symbol with its frequency, probability, and the actual Huffman code
assigned by the constructed tree (core/metrics.build_code_table_rows).
"""

from tkinter import ttk

from core.metrics import build_code_table_rows
from gui import theme


class CodeTableView(ttk.Frame):
    def __init__(self, parent, state):
        super().__init__(parent, style="TFrame")
        self.state = state
        self._build_ui()

    def _build_ui(self):
        header = ttk.Frame(self, style="Panel.TFrame")
        header.pack(fill="x", padx=12, pady=(12, 6))
        ttk.Label(header, text="Huffman Code Table", style="PanelHeading.TLabel").pack(
            anchor="w", padx=10, pady=10
        )

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
        for row in self.tree.get_children():
            self.tree.delete(row)

        if not self.state.frequencies:
            self.info_label.configure(
                text="Run the pipeline on the Compress tab to populate this table."
            )
            return

        rows = build_code_table_rows(self.state.frequencies, self.state.codes)
        for row in rows:
            display_symbol = _display_symbol(row["symbol"])
            self.tree.insert("", "end", values=(
                display_symbol,
                row["frequency"],
                f"{row['probability']:.4f}",
                row["code"] if row["code"] else "(not generated yet)",
                row["code_length"] if row["code"] else "-",
            ))

        self.info_label.configure(
            text=f"{len(rows)} distinct symbol(s). Table sorted by frequency (descending)."
        )


def _display_symbol(symbol):
    special = {" ": "SPACE", "\n": "\\n (newline)", "\t": "\\t (tab)", "\r": "\\r"}
    if symbol in special:
        return special[symbol]
    if symbol.isprintable():
        return symbol
    return f"U+{ord(symbol):04X}"
