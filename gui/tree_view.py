"""
gui/tree_view.py
-----------------
The "Huffman Tree" tab. Draws the ACTUAL constructed HuffmanNode tree
on a Tkinter Canvas -- not a static image. Every time the Compress tab
builds a new tree, `on_state_changed()` re-runs the layout algorithm
against the live tree object and redraws it.

Layout algorithm: a standard recursive "assign x by in-order leaf
position, y by depth" tree-drawing technique --
  - Leaves are placed left-to-right in the order an in-order traversal
    visits them, evenly spaced.
  - Internal nodes are placed at the horizontal midpoint of their
    children, one depth level below their parent.
This produces a clean, non-overlapping layout for trees of the sizes
a text-input demo will realistically produce.
"""

import tkinter as tk
from tkinter import ttk

from gui import theme

NODE_RADIUS = 22
LEVEL_HEIGHT = 90
LEAF_SPACING = 70
MARGIN_TOP = 40
MARGIN_LEFT = 60


class TreeView(ttk.Frame):
    def __init__(self, parent, state):
        super().__init__(parent, style="TFrame")
        self.state = state
        self._build_ui()

    def _build_ui(self):
        header = ttk.Frame(self, style="Panel.TFrame")
        header.pack(fill="x", padx=12, pady=(12, 6))
        ttk.Label(header, text="Huffman Tree Visualization", style="PanelHeading.TLabel").pack(
            anchor="w", padx=10, pady=10
        )

        self.info_label = ttk.Label(
            self, text="Run the pipeline on the Compress tab to see the tree here.",
            style="Muted.TLabel",
        )
        self.info_label.pack(anchor="w", padx=16, pady=(0, 6))

        canvas_frame = ttk.Frame(self, style="Panel.TFrame")
        canvas_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        h_scroll = ttk.Scrollbar(canvas_frame, orient="horizontal")
        v_scroll = ttk.Scrollbar(canvas_frame, orient="vertical")

        self.canvas = tk.Canvas(
            canvas_frame, bg=theme.BG_PANEL, highlightthickness=0,
            xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set,
        )
        h_scroll.configure(command=self.canvas.xview)
        v_scroll.configure(command=self.canvas.yview)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        canvas_frame.rowconfigure(0, weight=1)
        canvas_frame.columnconfigure(0, weight=1)

    # ------------------------------------------------------------------
    def on_state_changed(self):
        root = self.state.tree_root
        self.canvas.delete("all")

        if root is None:
            self.info_label.configure(
                text="Run the pipeline on the Compress tab to see the tree here."
            )
            self.canvas.configure(scrollregion=(0, 0, 400, 200))
            return

        # --- assign leaf x-positions via in-order traversal ------------
        positions = {}
        leaf_counter = [0]

        def assign_positions(node, depth):
            if node is None:
                return
            if node.is_leaf():
                x = MARGIN_LEFT + leaf_counter[0] * LEAF_SPACING
                leaf_counter[0] += 1
                positions[id(node)] = (x, MARGIN_TOP + depth * LEVEL_HEIGHT)
                return

            assign_positions(node.left, depth + 1)
            assign_positions(node.right, depth + 1)

            child_xs = []
            if node.left is not None:
                child_xs.append(positions[id(node.left)][0])
            if node.right is not None:
                child_xs.append(positions[id(node.right)][0])
            x = sum(child_xs) / len(child_xs) if child_xs else MARGIN_LEFT
            positions[id(node)] = (x, MARGIN_TOP + depth * LEVEL_HEIGHT)

        assign_positions(root, 0)

        max_x = max((p[0] for p in positions.values()), default=MARGIN_LEFT)
        max_y = max((p[1] for p in positions.values()), default=MARGIN_TOP)

        # --- draw edges first (so nodes render on top) ------------------
        def draw_edges(node):
            if node is None or node.is_leaf():
                return
            x0, y0 = positions[id(node)]
            for child, label in ((node.left, "0"), (node.right, "1")):
                if child is None:
                    continue
                x1, y1 = positions[id(child)]
                self.canvas.create_line(
                    x0, y0 + NODE_RADIUS, x1, y1 - NODE_RADIUS,
                    fill=theme.EDGE_COLOR, width=2,
                )
                mx, my = (x0 + x1) / 2, (y0 + y1) / 2
                self.canvas.create_oval(mx - 10, my - 10, mx + 10, my + 10,
                                         fill=theme.BG_PANEL, outline="")
                self.canvas.create_text(mx, my, text=label, fill=theme.ACCENT,
                                         font=theme.FONT_MONO_BOLD)
                draw_edges(child)

        draw_edges(root)

        # --- draw nodes ---------------------------------------------------
        def draw_nodes(node):
            if node is None:
                return
            x, y = positions[id(node)]
            if node.is_leaf():
                fill = theme.LEAF_FILL
                sym = node.symbol
                display_sym = _display_symbol(sym)
                label = f"{display_sym}\n{node.frequency}"
            else:
                fill = theme.INTERNAL_FILL
                label = f"{node.frequency}"

            self.canvas.create_oval(
                x - NODE_RADIUS, y - NODE_RADIUS, x + NODE_RADIUS, y + NODE_RADIUS,
                fill=fill, outline=theme.ACCENT, width=2,
            )
            self.canvas.create_text(
                x, y, text=label, fill=theme.FG_TEXT, font=theme.FONT_MONO, justify="center",
            )
            draw_nodes(node.left)
            draw_nodes(node.right)

        draw_nodes(root)

        self.canvas.configure(scrollregion=(0, 0, max_x + MARGIN_LEFT, max_y + 80))

        unique = len(self.state.frequencies)
        self.info_label.configure(
            text=f"Tree for {unique} unique symbol(s). Edge labels show the bit "
                 "appended when moving to that child (0 = left, 1 = right)."
        )


def _display_symbol(symbol):
    """Render whitespace/control characters visibly instead of blank."""
    if symbol is None:
        return "*"
    special = {
        " ": "'SPACE'",
        "\n": "'\\n'",
        "\t": "'\\t'",
        "\r": "'\\r'",
    }
    if symbol in special:
        return special[symbol]
    if symbol.isprintable():
        return repr(symbol)
    return f"U+{ord(symbol):04X}"
