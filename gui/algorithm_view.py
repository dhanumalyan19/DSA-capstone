"""
gui/algorithm_view.py
------------------------
The "Algorithm" / "How It Works" educational tab. Walks through the
narrated steps produced while building the tree for the user's actual
input (core/huffman.build_from_text's `steps`, extended with encoding
steps), with Next/Previous controls, exactly per project spec section 8.
"""

from tkinter import ttk

from gui import theme


class AlgorithmView(ttk.Frame):
    def __init__(self, parent, state):
        super().__init__(parent, style="TFrame")
        self.state = state
        self._steps = []
        self._index = 0
        self._build_ui()

    def _build_ui(self):
        header = ttk.Frame(self, style="Panel.TFrame")
        header.pack(fill="x", padx=12, pady=(12, 6))
        ttk.Label(header, text="How the Huffman Algorithm Works on Your Input",
                  style="PanelHeading.TLabel").pack(anchor="w", padx=10, pady=10)

        body = ttk.Frame(self, style="Panel.TFrame")
        body.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.step_label = ttk.Label(body, text="Step 0 of 0", style="PanelMuted.TLabel")
        self.step_label.pack(anchor="w", padx=10, pady=(10, 0))

        self.step_text = theme.styled_text_widget(body, height=16, width=100)
        self.step_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.step_text.configure(state="disabled")

        nav_row = ttk.Frame(body, style="Panel.TFrame")
        nav_row.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(nav_row, text="<< Previous", command=self._prev).pack(side="left")
        ttk.Button(nav_row, text="Next >>", style="Accent.TButton", command=self._next).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(nav_row, text="Jump to First", command=self._first).pack(side="left", padx=(16, 0))
        ttk.Button(nav_row, text="Jump to Last", command=self._last).pack(side="left", padx=(8, 0))

    def on_state_changed(self):
        steps = list(self.state.build_steps) + list(self.state.encode_steps)
        self._steps = steps if steps else [
            "No pipeline has been run yet. Go to the Compress tab, enter text, "
            "and click through Analyze -> Build Tree -> Generate Codes -> "
            "Compress. Come back here afterward to review each step that "
            "occurred, generated from your actual input."
        ]
        self._index = 0
        self._render()

    def _render(self):
        total = len(self._steps)
        self.step_label.configure(text=f"Step {self._index + 1} of {total}")
        self.step_text.configure(state="normal")
        self.step_text.delete("1.0", "end")
        self.step_text.insert("1.0", self._steps[self._index])
        self.step_text.configure(state="disabled")

    def _next(self):
        if self._index < len(self._steps) - 1:
            self._index += 1
            self._render()

    def _prev(self):
        if self._index > 0:
            self._index -= 1
            self._render()

    def _first(self):
        self._index = 0
        self._render()

    def _last(self):
        self._index = len(self._steps) - 1
        self._render()
