"""
gui/theme.py
------------
Centralized color palette / fonts / ttk styling so all six tabs look
like one coherent application instead of default-gray Tk widgets.

Palette: a calm "compression studio" theme -- deep slate background,
warm amber accent (evokes a physical signal/wire being compressed),
and a clean monospace for anything showing bits/codes so columns of
0s and 1s line up.
"""

import tkinter as tk
from tkinter import ttk

BG_DARK = "#1B2430"          # main window background
BG_PANEL = "#232E3D"         # card / panel background
BG_PANEL_LIGHT = "#2C3A4D"   # slightly raised panel
FG_TEXT = "#E7ECF3"          # primary text
FG_MUTED = "#93A2B7"         # secondary / muted text
ACCENT = "#E8A33D"           # amber accent (buttons, highlights)
ACCENT_DARK = "#C7862A"
GOOD = "#4CAF7D"             # success green (lossless PASS)
BAD = "#E5636B"              # failure red (FAILED)
LEAF_FILL = "#2E5F52"        # tree leaf node fill
INTERNAL_FILL = "#2C3A4D"    # tree internal node fill
EDGE_COLOR = "#93A2B7"

FONT_FAMILY = "Helvetica"
MONO_FAMILY = "Courier New"

FONT_TITLE = (FONT_FAMILY, 20, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 11)
FONT_HEADING = (FONT_FAMILY, 13, "bold")
FONT_BODY = (FONT_FAMILY, 10)
FONT_MONO = (MONO_FAMILY, 10)
FONT_MONO_BOLD = (MONO_FAMILY, 10, "bold")
FONT_BIG_RESULT = (FONT_FAMILY, 16, "bold")


def apply_theme(root):
    """Configure ttk styles once, at application start."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    root.configure(bg=BG_DARK)

    style.configure("TFrame", background=BG_DARK)
    style.configure("Panel.TFrame", background=BG_PANEL)
    style.configure("PanelLight.TFrame", background=BG_PANEL_LIGHT)

    style.configure("TLabel", background=BG_DARK, foreground=FG_TEXT, font=FONT_BODY)
    style.configure("Panel.TLabel", background=BG_PANEL, foreground=FG_TEXT, font=FONT_BODY)
    style.configure("Muted.TLabel", background=BG_DARK, foreground=FG_MUTED, font=FONT_BODY)
    style.configure("PanelMuted.TLabel", background=BG_PANEL, foreground=FG_MUTED, font=FONT_BODY)
    style.configure("Heading.TLabel", background=BG_DARK, foreground=FG_TEXT, font=FONT_HEADING)
    style.configure("PanelHeading.TLabel", background=BG_PANEL, foreground=FG_TEXT, font=FONT_HEADING)
    style.configure("Title.TLabel", background=BG_DARK, foreground=FG_TEXT, font=FONT_TITLE)
    style.configure("Subtitle.TLabel", background=BG_DARK, foreground=ACCENT, font=FONT_SUBTITLE)
    style.configure("Result.TLabel", background=BG_PANEL, foreground=ACCENT, font=FONT_BIG_RESULT)
    style.configure("Good.TLabel", background=BG_PANEL, foreground=GOOD, font=FONT_BIG_RESULT)
    style.configure("Bad.TLabel", background=BG_PANEL, foreground=BAD, font=FONT_BIG_RESULT)

    style.configure("Accent.TButton", font=(FONT_FAMILY, 10, "bold"), padding=8)
    style.map("Accent.TButton",
              background=[("!disabled", ACCENT), ("active", ACCENT_DARK)],
              foreground=[("!disabled", "#1B2430")])
    style.configure("TButton", font=FONT_BODY, padding=6)

    style.configure("TNotebook", background=BG_DARK, borderwidth=0)
    style.configure("TNotebook.Tab", background=BG_PANEL, foreground=FG_MUTED,
                     padding=(16, 8), font=(FONT_FAMILY, 10, "bold"))
    style.map("TNotebook.Tab",
              background=[("selected", ACCENT)],
              foreground=[("selected", "#1B2430")])

    style.configure("Treeview", background=BG_PANEL_LIGHT, fieldbackground=BG_PANEL_LIGHT,
                     foreground=FG_TEXT, rowheight=24, font=FONT_MONO, borderwidth=0)
    style.configure("Treeview.Heading", background=BG_PANEL, foreground=ACCENT,
                     font=(FONT_FAMILY, 10, "bold"))
    style.map("Treeview", background=[("selected", ACCENT_DARK)])

    style.configure("TEntry", fieldbackground=BG_PANEL_LIGHT, foreground=FG_TEXT,
                     insertcolor=FG_TEXT)
    style.configure("Horizontal.TProgressbar", background=ACCENT, troughcolor=BG_PANEL)

    return style


def styled_text_widget(parent, height=10, width=60, wrap="word"):
    """A tk.Text widget matching the dark theme (ttk has no Text widget)."""
    txt = tk.Text(
        parent, height=height, width=width, wrap=wrap,
        bg=BG_PANEL_LIGHT, fg=FG_TEXT, insertbackground=FG_TEXT,
        font=FONT_MONO, relief="flat", padx=8, pady=8,
        highlightthickness=1, highlightbackground="#3A4A60", highlightcolor=ACCENT,
    )
    return txt
