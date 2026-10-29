"""Dashboard: generate, browse, search, export and delete your records."""
import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox, ttk

from app import export, generator
from app.db import RECORD_FIELDS

COLUMNS = (
    # (field, heading, width)
    ("full_name", "Full Name", 190),
    ("address", "Address", 340),
    ("birthdate", "Birthdate", 100),
    ("mobile_number", "Mobile Number", 145),
    ("email", "Email", 250),
    ("gender", "Gender", 80),
    ("civil_status", "Civil Status", 105),
    ("occupation", "Occupation", 180),
    ("company", "Company", 230),
    ("fake_username", "Username", 170),
)
assert tuple(c[0] for c in COLUMNS) == RECORD_FIELDS


class DashboardFrame(ttk.Frame):
    def __init__(self, master, app, user):
        super().__init__(master, padding=(20, 16))
        self.app = app
        self.user_id = user["id"]
        self.username = user["username"]
        self.count_var = tk.StringVar(value=str(generator.MIN_RECORDS))
        self.search_var = tk.StringVar()
        self._search_job = None
        self.shown = []

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self._build_header()
        self._build_toolbar()
        self._build_table()
        self._build_footer()

        self.search_var.trace_add("write", lambda *_: self._schedule_search())
        self.refresh_theme()
        self.refresh()

    # ---- layout ------------------------------------------------------
    def _build_header(self):
        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Fake Data Generator", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, text=f"Logged in as {self.username}", style="Muted.TLabel").grid(
            row=1, column=0, sticky="w")
        right = ttk.Frame(header)
        right.grid(row=0, column=1, rowspan=2, sticky="e")
        self.theme_btn = ttk.Button(right, width=16, command=self.app.toggle_theme)
        self.theme_btn.grid(row=0, column=0, padx=(0, 8))
        ttk.Button(right, text="Log out", width=16, command=self.app.logout).grid(row=0, column=1)

    def _build_toolbar(self):
        bar = ttk.Frame(self)
        bar.grid(row=1, column=0, sticky="ew", pady=(16, 10))
        bar.columnconfigure(3, weight=1)

        ttk.Label(bar, text="Records to generate").grid(row=0, column=0, padx=(0, 8))
        digits_only = (self.register(lambda s: s.isdigit() and len(s) <= 4 or s == ""), "%P")
        self.count_spin = ttk.Spinbox(bar, from_=generator.MIN_RECORDS, to=generator.MAX_RECORDS,
                                      increment=10, width=7, textvariable=self.count_var,
                                      validate="key", validatecommand=digits_only)
        self.count_spin.grid(row=0, column=1)
        self.count_spin.bind("<Return>", lambda _e: self.generate())
        self.generate_btn = ttk.Button(bar, text="Generate", style="Accent.TButton", width=14,
                                       command=self.generate)
        self.generate_btn.grid(row=0, column=2, padx=(8, 0))

        ttk.Label(bar, text="Search").grid(row=0, column=4, padx=(0, 8))
        self.search_entry = ttk.Entry(bar, textvariable=self.search_var, width=30)
        self.search_entry.grid(row=0, column=5)
        self.search_entry.bind("<Escape>", lambda _e: self.search_var.set(""))
        ttk.Button(bar, text="Clear", width=14, command=lambda: self.search_var.set("")).grid(
            row=0, column=6, padx=(8, 0))

    def _build_table(self):
        card = ttk.Frame(self, style="Card.TFrame", padding=1)
        card.grid(row=2, column=0, sticky="nsew")
        card.columnconfigure(0, weight=1)
        card.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(card, columns=RECORD_FIELDS, show="headings", selectmode="extended")
        for field, heading, width in COLUMNS:
            self.tree.heading(field, text=heading, anchor="w")
            self.tree.column(field, width=width, minwidth=60, stretch=False, anchor="w")
        ysb = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        xsb = ttk.Scrollbar(card, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        xsb.grid(row=1, column=0, sticky="ew")

        self.empty_label = ttk.Label(card, style="Empty.TLabel", justify="center")
        self.tree.bind("<Delete>", lambda _e: self.delete_selected())
        self.tree.bind("<Control-a>", lambda _e: (self.tree.selection_set(self.tree.get_children()), "break")[1])
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._update_buttons())

    def _build_footer(self):
        foot = ttk.Frame(self)
        foot.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        foot.columnconfigure(1, weight=1)
        self.status = ttk.Label(foot, text="", style="Status.TLabel")
        self.status.grid(row=0, column=0, sticky="w")
        self.count_label = ttk.Label(foot, text="", style="Status.TLabel")
        self.count_label.grid(row=0, column=1, padx=12)
        self.export_btn = ttk.Button(foot, text="Export CSV", width=16, command=self.export_csv)
        self.export_btn.grid(row=0, column=2, padx=(0, 8))
        self.delete_btn = ttk.Button(foot, text="Delete selected", width=16, style="Danger.TButton",
                                     command=self.delete_selected)
        self.delete_btn.grid(row=0, column=3)

    # ---- behavior ----------------------------------------------------
    def set_status(self, text, kind="info"):
        style = {"info": "Status.TLabel", "error": "StatusError.TLabel", "ok": "StatusOk.TLabel"}[kind]
        self.status.configure(text=text, style=style)

    def refresh_theme(self):
        palette = self.app.palette
        self.theme_btn.configure(text="Light mode" if self.app.theme == "dark" else "Dark mode")
        self.tree.tag_configure("odd", background=palette["row_alt"])
        self.tree.tag_configure("even", background=palette["surface"])

    def _schedule_search(self):
        if self._search_job:
            self.after_cancel(self._search_job)
        self._search_job = self.after(200, self.refresh)

    def refresh(self):
        self._search_job = None
        search = self.search_var.get().strip()
        self.shown = self.app.db.list_records(self.user_id, search)
        total = self.app.db.count_records(self.user_id)

        self.tree.delete(*self.tree.get_children())
        for i, row in enumerate(self.shown):
            self.tree.insert("", "end", iid=str(row["id"]), values=[row[f] for f in RECORD_FIELDS],
                             tags=("odd" if i % 2 else "even",))

        if total == 0:
            self.empty_label.configure(text="No records yet.\nSet how many you want, then hit Generate.")
            self.empty_label.place(relx=0.5, rely=0.5, anchor="center")
        elif not self.shown:
            self.empty_label.configure(text=f"No records match “{search}”.")
            self.empty_label.place(relx=0.5, rely=0.5, anchor="center")
        else:
            self.empty_label.place_forget()

        if search:
            self.count_label.configure(text=f"Showing {len(self.shown)} of {total} records")
        else:
            self.count_label.configure(text=f"{total} record{'s' if total != 1 else ''}")
        self._update_buttons()

    def _update_buttons(self):
        self.delete_btn.state(["!disabled"] if self.tree.selection() else ["disabled"])
        self.export_btn.state(["!disabled"] if self.shown else ["disabled"])

    def generate(self):
        try:
            count = int(self.count_var.get())
            records = generator.generate_records(count)
        except ValueError:
            self.set_status(f"Enter a number from {generator.MIN_RECORDS} to {generator.MAX_RECORDS}.",
                            "error")
            return
        saved = self.app.db.insert_records(self.user_id, records)
        self.search_var.set("")
        self.refresh()
        self.set_status(f"Generated and saved {saved} records.", "ok")

    def delete_selected(self):
        ids = self.tree.selection()
        if not ids:
            return
        noun = "record" if len(ids) == 1 else "records"
        if not messagebox.askyesno("Delete records", f"Delete {len(ids)} selected {noun}? This can't be undone.",
                                   parent=self):
            return
        deleted = self.app.db.delete_records(self.user_id, ids)
        self.refresh()
        self.set_status(f"Deleted {deleted} {noun}.", "ok")

    def export_csv(self):
        if not self.shown:
            return
        path = filedialog.asksaveasfilename(
            parent=self, title="Export records", defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"fake_records_{self.username}_{date.today():%Y%m%d}.csv")
        if not path:
            return
        try:
            count = export.write_csv(path, self.shown)
        except OSError as exc:
            self.set_status(f"Export failed: {exc.strerror or exc}", "error")
            return
        self.set_status(f"Exported {count} records to {path}", "ok")
