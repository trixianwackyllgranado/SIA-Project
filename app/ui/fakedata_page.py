"""Fake Data tool: generate, browse, search, export, email and delete records."""
import os
import tempfile
import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox, ttk

from app import export, generator
from app.db import RECORD_FIELDS
from app.ui.common import Page, fill_table, make_table, stripe_table

COLUMNS = (
    # (field, heading, width, stretch)
    ("full_name", "Full Name", 190, False),
    ("address", "Address", 340, False),
    ("birthdate", "Birthdate", 100, False),
    ("mobile_number", "Mobile Number", 145, False),
    ("email", "Email", 250, False),
    ("gender", "Gender", 80, False),
    ("civil_status", "Civil Status", 105, False),
    ("occupation", "Occupation", 180, False),
    ("company", "Company", 230, False),
    ("fake_username", "Username", 170, False),
)
assert tuple(c[0] for c in COLUMNS) == RECORD_FIELDS


class FakeDataPage(Page):
    title = "Fake Data"
    subtitle = "Generate Philippine sample records for testing. Saved to your account."

    def __init__(self, master, shell):
        super().__init__(master, shell)
        self.count_var = tk.StringVar(value=str(generator.MIN_RECORDS))
        self.search_var = tk.StringVar()
        self._search_job = None
        self.shown = []

        self.rowconfigure(2, weight=1)
        self._build_toolbar()
        self._build_table()
        self._build_footer()
        self.search_var.trace_add("write", lambda *_: self._schedule_search())
        self.refresh()

    # ---- layout ------------------------------------------------------
    def _build_toolbar(self):
        bar = ttk.Frame(self)
        bar.grid(row=1, column=0, sticky="ew", pady=(0, 10))
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
        self.search_entry = ttk.Entry(bar, textvariable=self.search_var, width=28)
        self.search_entry.grid(row=0, column=5)
        self.search_entry.bind("<Escape>", lambda _e: self.search_var.set(""))
        ttk.Button(bar, text="Clear", width=14, command=lambda: self.search_var.set("")).grid(
            row=0, column=6, padx=(8, 0))

    def _build_table(self):
        card, self.tree = make_table(self, COLUMNS)
        card.grid(row=2, column=0, sticky="nsew")
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
        self.email_btn = ttk.Button(foot, text="Email CSV", width=16, command=self.email_csv)
        self.email_btn.grid(row=0, column=3, padx=(0, 8))
        self.delete_btn = ttk.Button(foot, text="Delete selected", width=16, style="Danger.TButton",
                                     command=self.delete_selected)
        self.delete_btn.grid(row=0, column=4)

    # ---- behavior ----------------------------------------------------
    def refresh_theme(self):
        stripe_table(self.tree, self.app.palette)

    def _schedule_search(self):
        if self._search_job:
            self.after_cancel(self._search_job)
        self._search_job = self.after(200, self.refresh)

    def refresh(self):
        self._search_job = None
        search = self.search_var.get().strip()
        self.shown = self.db.list_records(self.user_id, search)
        total = self.db.count_records(self.user_id)
        fill_table(self.tree, [(row["id"], [row[f] for f in RECORD_FIELDS]) for row in self.shown])

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
        has_rows = ["!disabled"] if self.shown else ["disabled"]
        self.export_btn.state(has_rows)
        self.email_btn.state(has_rows)

    def generate(self):
        try:
            count = int(self.count_var.get())
            records = generator.generate_records(count)
        except ValueError:
            self.set_status(f"Enter a number from {generator.MIN_RECORDS} to {generator.MAX_RECORDS}.",
                            "error")
            return
        saved = self.db.insert_records(self.user_id, records)
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
        deleted = self.db.delete_records(self.user_id, ids)
        self.refresh()
        self.set_status(f"Deleted {deleted} {noun}.", "ok")

    def _csv_name(self):
        return f"fake_records_{self.username}_{date.today():%Y%m%d}.csv"

    def export_csv(self):
        if not self.shown:
            return
        path = filedialog.asksaveasfilename(
            parent=self, title="Export records", defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")], initialfile=self._csv_name())
        if not path:
            return
        try:
            count = export.write_csv(path, self.shown)
        except OSError as exc:
            self.set_status(f"Export failed: {exc.strerror or exc}", "error")
            return
        self.set_status(f"Exported {count} records to {os.path.basename(path)}.", "ok")

    def email_csv(self):
        """Write the records shown to a temporary CSV and open it in the Email tool."""
        if not self.shown:
            return
        folder = tempfile.mkdtemp(prefix="utilityhub-")
        path = os.path.join(folder, self._csv_name())
        try:
            count = export.write_csv(path, self.shown)
        except OSError as exc:
            self.set_status(f"Couldn't prepare the CSV: {exc.strerror or exc}", "error")
            return
        self.shell.compose_email(
            subject="Fake data records",
            body=f"Attached are {count} generated sample records (fake data for testing).",
            attachment=path)
