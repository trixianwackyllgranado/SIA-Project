"""Light/dark palettes, ttk styles, fonts and the window icon."""
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

PALETTES = {
    "light": {
        "bg": "#F3F5F9", "surface": "#FFFFFF", "text": "#1E2430", "muted": "#5E6779",
        "border": "#D6DBE4", "input": "#FFFFFF", "accent": "#2F6FEB", "accent_hover": "#2459C4",
        "accent_fg": "#FFFFFF", "danger": "#C93C3C", "danger_hover": "#A93030",
        "success": "#1F8A4C", "select": "#D9E6FF", "row_alt": "#F7F9FC", "heading": "#EDF0F5",
    },
    "dark": {
        "bg": "#141821", "surface": "#1D232E", "text": "#E5E9F0", "muted": "#99A2B3",
        "border": "#333B4B", "input": "#151A23", "accent": "#5B8DEF", "accent_hover": "#4677DB",
        "accent_fg": "#FFFFFF", "danger": "#E06666", "danger_hover": "#C95252",
        "success": "#4CC38A", "select": "#2B3D61", "row_alt": "#222937", "heading": "#262D3B",
    },
}

_FONT_CANDIDATES = ("Segoe UI", "Inter", "Helvetica Neue", "Noto Sans", "DejaVu Sans", "Arial")


def _pick_family(root):
    available = set(tkfont.families(root))
    for family in _FONT_CANDIDATES:
        if family in available:
            return family
    return tkfont.nametofont("TkDefaultFont").actual("family")


def setup_fonts(root):
    family = _pick_family(root)
    return {
        "body": (family, 10),
        "small": (family, 9),
        "bold": (family, 10, "bold"),
        "title": (family, 18, "bold"),
        "subtitle": (family, 11),
        "empty": (family, 12),
    }


def apply_theme(root, name, fonts):
    """Restyle every ttk widget for palette `name`. Returns the palette dict."""
    p = PALETTES[name]
    style = ttk.Style(root)
    style.theme_use("clam")
    root.configure(background=p["bg"])

    style.configure(".", background=p["bg"], foreground=p["text"], font=fonts["body"],
                    bordercolor=p["border"], lightcolor=p["border"], darkcolor=p["border"],
                    troughcolor=p["bg"], focuscolor=p["accent"], insertcolor=p["text"])

    # Frames
    style.configure("TFrame", background=p["bg"])
    style.configure("Card.TFrame", background=p["surface"], relief="solid", borderwidth=1)
    style.configure("Plain.Card.TFrame", background=p["surface"], relief="flat", borderwidth=0)

    # Labels on the page background
    style.configure("TLabel", background=p["bg"], foreground=p["text"])
    style.configure("Muted.TLabel", background=p["bg"], foreground=p["muted"])
    style.configure("Title.TLabel", background=p["bg"], foreground=p["text"], font=fonts["title"])
    style.configure("Status.TLabel", background=p["bg"], foreground=p["muted"], font=fonts["small"])
    style.configure("StatusError.TLabel", background=p["bg"], foreground=p["danger"], font=fonts["small"])
    style.configure("StatusOk.TLabel", background=p["bg"], foreground=p["success"], font=fonts["small"])

    # Labels on cards
    style.configure("Card.TLabel", background=p["surface"], foreground=p["text"])
    style.configure("CardBold.TLabel", background=p["surface"], foreground=p["text"], font=fonts["bold"])
    style.configure("CardMuted.TLabel", background=p["surface"], foreground=p["muted"], font=fonts["subtitle"])
    style.configure("CardTitle.TLabel", background=p["surface"], foreground=p["text"], font=fonts["title"])
    style.configure("CardError.TLabel", background=p["surface"], foreground=p["danger"])
    style.configure("CardSuccess.TLabel", background=p["surface"], foreground=p["success"])
    style.configure("Empty.TLabel", background=p["surface"], foreground=p["muted"], font=fonts["empty"])

    # Buttons
    style.configure("TButton", background=p["surface"], foreground=p["text"], padding=(14, 7),
                    borderwidth=1, relief="flat")
    style.map("TButton", background=[("disabled", p["bg"]), ("pressed", p["heading"]), ("active", p["heading"])],
              foreground=[("disabled", p["muted"])])
    style.configure("Accent.TButton", background=p["accent"], foreground=p["accent_fg"],
                    bordercolor=p["accent"], font=fonts["bold"])
    style.map("Accent.TButton", background=[("disabled", p["border"]), ("pressed", p["accent_hover"]),
                                            ("active", p["accent_hover"])],
              bordercolor=[("active", p["accent_hover"])])
    style.configure("Danger.TButton", background=p["surface"], foreground=p["danger"], bordercolor=p["danger"])
    style.map("Danger.TButton", background=[("pressed", p["danger_hover"]), ("active", p["danger"])],
              foreground=[("active", p["accent_fg"]), ("pressed", p["accent_fg"])])

    # Inputs
    for widget in ("TEntry", "TSpinbox"):
        style.configure(widget, fieldbackground=p["input"], foreground=p["text"], padding=6,
                        insertcolor=p["text"], arrowcolor=p["text"], background=p["surface"])
        style.map(widget, bordercolor=[("focus", p["accent"])], lightcolor=[("focus", p["accent"])],
                  fieldbackground=[("readonly", p["input"])])
    style.configure("Card.TCheckbutton", background=p["surface"], foreground=p["muted"],
                    indicatorbackground=p["input"], indicatorforeground=p["accent"])
    style.map("Card.TCheckbutton", background=[("active", p["surface"])],
              indicatorbackground=[("selected", p["input"])])

    # Table
    style.configure("Treeview", background=p["surface"], fieldbackground=p["surface"],
                    foreground=p["text"], rowheight=28, borderwidth=0)
    style.map("Treeview", background=[("selected", p["select"])], foreground=[("selected", p["text"])])
    style.configure("Treeview.Heading", background=p["heading"], foreground=p["text"],
                    font=fonts["bold"], relief="flat", padding=(8, 6))
    style.map("Treeview.Heading", background=[("active", p["border"])])
    style.configure("TScrollbar", background=p["heading"], troughcolor=p["surface"],
                    arrowcolor=p["muted"], bordercolor=p["surface"])
    return p


def make_icon(root, accent="#2F6FEB"):
    """A 32x32 'table' icon drawn in code, so the app ships no image files."""
    size = 32
    img = tk.PhotoImage(master=root, width=size, height=size)
    img.put(accent, to=(2, 2, size - 2, size - 2))
    for y in (9, 15, 21):
        img.put("#FFFFFF", to=(7, y, size - 7, y + 3))
    img.put("#FFFFFF", to=(12, 9, 14, 24))  # first column divider
    return img
