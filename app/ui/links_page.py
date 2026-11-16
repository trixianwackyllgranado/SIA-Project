"""URL Shortener tool: shorten links with is.gd and keep a history."""
import tkinter as tk
import webbrowser
from tkinter import messagebox, ttk

from app import shortener
from app.ui.common import Page, fill_table, make_table, one_line, run_in_background, stripe_table

COLUMNS = (
    ("short_url", "Short link", 200, False),
    ("long_url", "Original link", 520, True),
    ("created_at", "Created", 150, False),
)


class LinksPage(Page):
    title = "URL Shortener"
    subtitle = "Turn long links into short ones with the is.gd API. Your links are saved here."

    def __init__(self, master, shell):
        super().__init__(master, shell)
        self.url_var = tk.StringVar()
        self.result_var = tk.StringVar()
        self.links = {}  # row id -> row, for the selected-row buttons

        self.rowconfigure(4, weight=1)
        self._build_form()
        ttk.Label(self, text="History", style="Section.TLabel").grid(row=3, column=0, sticky="w", pady=(18, 6))
        card, self.tree = make_table(self, COLUMNS)
        card.grid(row=4, column=0, sticky="nsew")
        self.empty_label = ttk.Label(card, text="No short links yet.", style="Empty.TLabel")
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._update_buttons())
        self.tree.bind("<Double-1>", lambda _e: self.copy_selected())
        self.tree.bind("<Delete>", lambda _e: self.delete_selected())
        self._build_footer()
        self.refresh()

    def _build_form(self):
        form = ttk.Frame(self, style="Card.TFrame", padding=16)
        form.grid(row=1, column=0, sticky="ew")
        form.columnconfigure(0, weight=1)
        ttk.Label(form, text="Long link", style="CardBold.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.url_entry = ttk.Entry(form, textvariable=self.url_var)
        self.url_entry.grid(row=1, column=0, sticky="ew")
        self.url_entry.bind("<Return>", lambda _e: self.shorten())
        self.shorten_btn = ttk.Button(form, text="Shorten", style="Accent.TButton", width=14,
                                      command=self.shorten)
        self.shorten_btn.grid(row=1, column=1, padx=(8, 0))

        # Shown after a link is shortened.
        self.result_row = ttk.Frame(form, style="Plain.Card.TFrame")
        self.result_row.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        self.result_row.columnconfigure(1, weight=1, minsize=190)
        ttk.Label(self.result_row, text="Short link", style="CardBold.TLabel").grid(row=0, column=0, padx=(0, 10))
        ttk.Label(self.result_row, textvariable=self.result_var, style="CardLink.TLabel").grid(
            row=0, column=1, sticky="w")
        actions = (("Copy", self.copy_result), ("Open", self.open_result),
                   ("Send by email", self.email_result), ("Send by SMS", self.sms_result))
        for col, (label, command) in enumerate(actions, start=2):
            ttk.Button(self.result_row, text=label, width=12, command=command).grid(row=0, column=col, padx=(8, 0))
        self.result_row.grid_remove()

    def _build_footer(self):
        foot = ttk.Frame(self)
        foot.grid(row=5, column=0, sticky="ew", pady=(10, 0))
        foot.columnconfigure(0, weight=1)
        self.status = ttk.Label(foot, text="", style="Status.TLabel")
        self.status.grid(row=0, column=0, sticky="w")
        self.copy_btn = ttk.Button(foot, text="Copy short link", width=16, command=self.copy_selected)
        self.copy_btn.grid(row=0, column=1, padx=(0, 8))
        self.open_btn = ttk.Button(foot, text="Open original", width=16, command=self.open_selected)
        self.open_btn.grid(row=0, column=2, padx=(0, 8))
        self.delete_btn = ttk.Button(foot, text="Delete selected", width=16, style="Danger.TButton",
                                     command=self.delete_selected)
        self.delete_btn.grid(row=0, column=3)

    # ---- behavior ----------------------------------------------------
    def refresh_theme(self):
        stripe_table(self.tree, self.app.palette)

    def on_show(self):
        self.url_entry.focus_set()

    def refresh(self):
        rows = self.db.list_links(self.user_id)
        self.links = {str(r["id"]): r for r in rows}
        fill_table(self.tree, [(r["id"], [r["short_url"], one_line(r["long_url"], 90), r["created_at"]])
                               for r in rows])
        if rows:
            self.empty_label.place_forget()
        else:
            self.empty_label.place(relx=0.5, rely=0.5, anchor="center")
        self._update_buttons()

    def _update_buttons(self):
        selected = self.tree.selection()
        one = ["!disabled"] if len(selected) == 1 else ["disabled"]
        self.copy_btn.state(one)
        self.open_btn.state(one)
        self.delete_btn.state(["!disabled"] if selected else ["disabled"])

    def shorten(self):
        try:
            long_url = shortener.clean_url(self.url_var.get())
        except shortener.ShortenerError as exc:
            self.set_status(str(exc), "error")
            return
        # is.gd asks clients not to resubmit the same URL, so reuse a saved one.
        existing = self.db.find_link(self.user_id, long_url)
        if existing:
            self._show_result(existing["short_url"])
            self.set_status("You already shortened this link, so the saved one is shown.", "info")
            return
        self.shorten_btn.state(["disabled"])
        self.set_status("Shortening...")
        run_in_background(self.app, lambda: shortener.shorten(long_url), self._shortened)

    def _shortened(self, result, error):
        if not self.winfo_exists():
            if result:  # logged out mid-request: still keep the link
                self.db.add_link(self.user_id, *result)
            return
        self.shorten_btn.state(["!disabled"])
        if error:
            message = str(error) if isinstance(error, shortener.ShortenerError) else "Something went wrong."
            self.set_status(message, "error")
            return
        long_url, short_url = result
        self.db.add_link(self.user_id, long_url, short_url)
        self.url_var.set("")
        self._show_result(short_url)
        self.refresh()
        self.set_status("Short link created and saved.", "ok")

    def _show_result(self, short_url):
        self.result_var.set(short_url)
        self.result_row.grid()

    def _copy(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.set_status(f"Copied {text}", "ok")

    def _selected_link(self):
        selected = self.tree.selection()
        return self.links.get(selected[0]) if len(selected) == 1 else None

    def copy_result(self):
        self._copy(self.result_var.get())

    def open_result(self):
        webbrowser.open_new_tab(self.result_var.get())

    def email_result(self):
        self.shell.compose_email(subject="Link", body=self.result_var.get())

    def sms_result(self):
        self.shell.compose_sms(body=self.result_var.get())

    def copy_selected(self):
        link = self._selected_link()
        if link:
            self._copy(link["short_url"])

    def open_selected(self):
        link = self._selected_link()
        if link:
            webbrowser.open_new_tab(link["long_url"])

    def delete_selected(self):
        ids = self.tree.selection()
        if not ids:
            return
        noun = "link" if len(ids) == 1 else "links"
        if not messagebox.askyesno("Delete links", f"Delete {len(ids)} saved {noun} from your history?\n"
                                   "The short link itself keeps working on is.gd.", parent=self):
            return
        deleted = self.db.delete_links(self.user_id, ids)
        self.refresh()
        self.set_status(f"Deleted {deleted} {noun}.", "ok")
