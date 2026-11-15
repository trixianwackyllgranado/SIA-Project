"""Pieces every tool page shares: the page header, status line, history table
and running network calls without freezing the window."""
import queue
import threading
import tkinter as tk
from tkinter import ttk


def run_in_background(root, work, on_done):
    """Run work() on a worker thread, then call on_done(result, error) on the Tk thread.

    Network calls take a few seconds; running them here keeps the window
    responsive. SQLite is only touched in on_done, on the main thread.
    """
    box = queue.Queue(maxsize=1)

    def worker():
        try:
            box.put((work(), None))
        except Exception as exc:  # handed to on_done, never lost
            box.put((None, exc))

    def poll():
        try:
            result, error = box.get_nowait()
        except queue.Empty:
            root.after(100, poll)
            return
        on_done(result, error)

    threading.Thread(target=worker, daemon=True).start()
    root.after(100, poll)


class Page(ttk.Frame):
    """Base for the four tool pages: title, subtitle and a status line."""

    title = ""
    subtitle = ""

    def __init__(self, master, shell):
        super().__init__(master, padding=(24, 20))
        self.shell = shell
        self.app = shell.app
        self.db = shell.app.db
        self.user_id = shell.user["id"]
        self.username = shell.user["username"]
        self.columnconfigure(0, weight=1)

        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        ttk.Label(header, text=self.title, style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, text=self.subtitle, style="Muted.TLabel").grid(row=1, column=0, sticky="w")

    def set_status(self, text, kind="info"):
        style = {"info": "Status.TLabel", "error": "StatusError.TLabel", "ok": "StatusOk.TLabel"}[kind]
        self.status.configure(text=text, style=style)

    def on_show(self):
        """Called each time the sidebar switches to this page."""

    def refresh_theme(self):
        """Re-color anything ttk styles don't reach (Text widgets, table stripes)."""


def make_table(parent, columns, height=8):
    """A Treeview with scrollbars inside a bordered card.

    `columns` is a list of (key, heading, width, stretch). Returns (card, tree).
    """
    card = ttk.Frame(parent, style="Card.TFrame", padding=1)
    card.columnconfigure(0, weight=1)
    card.rowconfigure(0, weight=1)
    tree = ttk.Treeview(card, columns=[c[0] for c in columns], show="headings",
                        selectmode="extended", height=height)
    for key, heading, width, stretch in columns:
        tree.heading(key, text=heading, anchor="w")
        tree.column(key, width=width, minwidth=60, stretch=stretch, anchor="w")
    ysb = ttk.Scrollbar(card, orient="vertical", command=tree.yview)
    xsb = ttk.Scrollbar(card, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
    tree.grid(row=0, column=0, sticky="nsew")
    ysb.grid(row=0, column=1, sticky="ns")
    xsb.grid(row=1, column=0, sticky="ew")
    return card, tree


def fill_table(tree, rows):
    """Replace the table contents. `rows` is a list of (row_id, values)."""
    tree.delete(*tree.get_children())
    for i, (row_id, values) in enumerate(rows):
        tree.insert("", "end", iid=str(row_id), values=values, tags=("odd" if i % 2 else "even",))


def stripe_table(tree, palette):
    tree.tag_configure("odd", background=palette["row_alt"])
    tree.tag_configure("even", background=palette["surface"])


def make_text(parent, height):
    """A multi-line input (ttk has none, so it is a tk.Text styled by style_text)."""
    return tk.Text(parent, height=height, wrap="word", relief="flat", undo=True,
                   highlightthickness=1, padx=8, pady=6)


def style_text(widget, palette, font):
    widget.configure(background=palette["input"], foreground=palette["text"],
                     insertbackground=palette["text"], selectbackground=palette["select"],
                     selectforeground=palette["text"], highlightbackground=palette["border"],
                     highlightcolor=palette["accent"], font=font)


def text_value(widget):
    return widget.get("1.0", "end-1c")


def set_text_value(widget, value):
    widget.delete("1.0", "end")
    widget.insert("1.0", value)


def one_line(text, limit=60):
    """Shorten text for a table cell: newlines become spaces, long text gets '...'."""
    flat = " ".join(str(text).split())
    return flat if len(flat) <= limit else flat[: limit - 3] + "..."
