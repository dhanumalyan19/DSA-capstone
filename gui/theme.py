"""
gui/theme.py
------------
Centralized palette / fonts / ttk styling so all six tabs look like one
coherent desktop application instead of default-gray Tk widgets.
"""

import tkinter as tk
from tkinter import ttk

BG_DARK = "#101418"          # main window background
BG_PANEL = "#171C22"         # card / panel background
BG_PANEL_LIGHT = "#202832"   # slightly raised panel
BG_INPUT = "#0F141A"
FG_TEXT = "#F4F7FA"          # primary text
FG_MUTED = "#A8B1BD"         # secondary / muted text
FG_FAINT = "#75808D"
ACCENT = "#4DD0B5"           # primary action / highlights
ACCENT_DARK = "#29A891"
ACCENT_WARM = "#F2B84B"      # secondary highlight
GOOD = "#63D489"             # success green (lossless PASS)
BAD = "#FF6B6B"              # failure red (FAILED)
BORDER = "#2E3A46"
LEAF_FILL = "#1F6F5C"        # tree leaf node fill
INTERNAL_FILL = "#263241"    # tree internal node fill
EDGE_COLOR = "#8A96A5"

FONT_FAMILY = "Helvetica"
MONO_FAMILY = "Courier New"

FONT_TITLE = (FONT_FAMILY, 20, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 11)
FONT_HEADING = (FONT_FAMILY, 13, "bold")
FONT_BODY = (FONT_FAMILY, 10)
FONT_SMALL = (FONT_FAMILY, 9)
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
    style.configure("Header.TFrame", background=BG_DARK)
    style.configure("Panel.TFrame", background=BG_PANEL)
    style.configure("PanelLight.TFrame", background=BG_PANEL_LIGHT)
    style.configure("Metric.TFrame", background=BG_PANEL_LIGHT, relief="flat")

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
    style.configure("MetricLabel.TLabel", background=BG_PANEL_LIGHT, foreground=FG_MUTED,
                    font=(FONT_FAMILY, 8, "bold"))
    style.configure("MetricValue.TLabel", background=BG_PANEL_LIGHT, foreground=FG_TEXT,
                    font=(FONT_FAMILY, 14, "bold"))
    style.configure("MetricDetail.TLabel", background=BG_PANEL_LIGHT, foreground=FG_FAINT,
                    font=FONT_SMALL)

    style.configure("Accent.TButton", font=(FONT_FAMILY, 10, "bold"), padding=8)
    style.map("Accent.TButton",
              background=[("!disabled", ACCENT), ("active", ACCENT_DARK)],
              foreground=[("!disabled", "#101418"), ("disabled", FG_FAINT)])
    style.configure("TButton", font=FONT_BODY, padding=6)
    style.map("TButton",
              background=[("active", BG_PANEL_LIGHT), ("disabled", BG_PANEL)],
              foreground=[("disabled", FG_FAINT)])

    style.configure("TNotebook", background=BG_DARK, borderwidth=0)
    style.configure("TNotebook.Tab", background=BG_PANEL, foreground=FG_MUTED,
                     padding=(18, 10), font=(FONT_FAMILY, 10, "bold"))
    style.map("TNotebook.Tab",
              background=[("selected", ACCENT)],
              foreground=[("selected", "#101418")])

    style.configure("Treeview", background=BG_PANEL_LIGHT, fieldbackground=BG_PANEL_LIGHT,
                     foreground=FG_TEXT, rowheight=24, font=FONT_MONO, borderwidth=0)
    style.configure("Treeview.Heading", background=BG_PANEL, foreground=ACCENT,
                     font=(FONT_FAMILY, 10, "bold"))
    style.map("Treeview", background=[("selected", ACCENT_DARK)])

    style.configure("TEntry", fieldbackground=BG_INPUT, foreground=FG_TEXT,
                     insertcolor=FG_TEXT)
    style.configure("Horizontal.TProgressbar", background=ACCENT, troughcolor=BG_PANEL)
    style.configure("Vertical.TScrollbar", background=BG_PANEL_LIGHT, troughcolor=BG_PANEL)
    style.configure("Horizontal.TScrollbar", background=BG_PANEL_LIGHT, troughcolor=BG_PANEL)

    return style


def styled_text_widget(parent, height=10, width=60, wrap="word"):
    """A tk.Text widget matching the dark theme (ttk has no Text widget)."""
    txt = tk.Text(
        parent, height=height, width=width, wrap=wrap,
        bg=BG_INPUT, fg=FG_TEXT, insertbackground=FG_TEXT,
        font=FONT_MONO, relief="flat", padx=8, pady=8,
        highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT,
    )
    return txt


def metric_card(parent, label, value_var, detail_var=None):
    """Create a compact status card and return its frame."""
    card = ttk.Frame(parent, style="Metric.TFrame")
    ttk.Label(card, text=label.upper(), style="MetricLabel.TLabel").pack(
        anchor="w", padx=12, pady=(10, 0)
    )
    ttk.Label(card, textvariable=value_var, style="MetricValue.TLabel").pack(
        anchor="w", padx=12, pady=(2, 0)
    )
    if detail_var is not None:
        ttk.Label(card, textvariable=detail_var, style="MetricDetail.TLabel").pack(
            anchor="w", padx=12, pady=(1, 10)
        )
    else:
        ttk.Label(card, text="", style="MetricDetail.TLabel").pack(
            anchor="w", padx=12, pady=(1, 10)
        )
    return card
