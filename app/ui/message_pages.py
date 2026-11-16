"""Email and SMS tools. Both work the same way: fill the form, confirm, send in
the background, and log the result (sent or failed) to the user's history."""
import os
import shutil
import tempfile
import tkinter as tk
from tkinter import messagebox, ttk

from app import config, mailer, sms_gateway
from app.ui.common import (Page, fill_table, make_table, make_text, one_line, run_in_background,
                           set_text_value, stripe_table, style_text, text_value)


class MessagePage(Page):
    channel = ""            # "email" or "sms", as stored in the messages table
    required = ()           # .env names this tool needs
    error_type = Exception  # the module's user-safe error class
    columns = ()

    def __init__(self, master, shell):
        super().__init__(master, shell)
        self.settings = config.load()
        self.sending = False
        self.text_widgets = []

        self.rowconfigure(5, weight=1)
        self._build_banner()
        form = ttk.Frame(self, style="Card.TFrame", padding=16)
        form.grid(row=2, column=0, sticky="ew")
        form.columnconfigure((0, 1), weight=1, uniform="half")
        self.build_fields(form)

        ttk.Label(self, text="History", style="Section.TLabel").grid(row=4, column=0, sticky="w", pady=(18, 6))
        card, self.tree = make_table(self, self.columns, height=6)
        card.grid(row=5, column=0, sticky="nsew")
        self.empty_label = ttk.Label(card, text="Nothing sent yet.", style="Empty.TLabel")
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._update_buttons())
        self.tree.bind("<Delete>", lambda _e: self.delete_selected())

        foot = ttk.Frame(self)
        foot.grid(row=6, column=0, sticky="ew", pady=(10, 0))
        foot.columnconfigure(0, weight=1)
        self.status = ttk.Label(foot, text="", style="Status.TLabel")
        self.status.grid(row=0, column=0, sticky="w")
        self.delete_btn = ttk.Button(foot, text="Delete selected", width=16, style="Danger.TButton",
                                     command=self.delete_selected)
        self.delete_btn.grid(row=0, column=1)

        self.check_setup()
        self.refresh()

    # ---- pieces each tool fills in -----------------------------------
    def build_fields(self, form):
        raise NotImplementedError

    def collect(self):
        """Validate the form. Return (recipient_for_confirm, values) or raise error_type."""
        raise NotImplementedError

    def send(self, settings, values):
        """Runs on the worker thread. Return the recipient as it was sent."""
        raise NotImplementedError

    def log_values(self, values):
        """(subject, body) to store in the history."""
        raise NotImplementedError

    def row_values(self, row):
        raise NotImplementedError

    def clear_form(self):
        raise NotImplementedError

    # ---- shared layout -----------------------------------------------
    def _build_banner(self):
        self.banner = ttk.Frame(self, style="Banner.TFrame", padding=(14, 10))
        self.banner.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        self.banner.columnconfigure(0, weight=1)
        self.banner_label = ttk.Label(self.banner, style="Banner.TLabel", justify="left", wraplength=640)
        self.banner_label.grid(row=0, column=0, sticky="w")
        ttk.Button(self.banner, text="Check again", width=14, command=self.check_setup).grid(row=0, column=1)

    def make_buttons(self, form, row):
        """Clear | Send, the same width, aligned right under the form."""
        buttons = ttk.Frame(form, style="Plain.Card.TFrame")
        buttons.grid(row=row, column=1, sticky="e", pady=(12, 0))
        ttk.Button(buttons, text="Clear", width=14, command=self.clear_form).grid(row=0, column=0, padx=(0, 8))
        self.send_btn = ttk.Button(buttons, text="Send", style="Accent.TButton", width=14,
                                   command=self.confirm_and_send)
        self.send_btn.grid(row=0, column=1)

    def add_text(self, form, height):
        widget = make_text(form, height)
        self.text_widgets.append(widget)
        style_text(widget, self.app.palette, self.app.fonts["body"])
        return widget

    # ---- shared behavior ---------------------------------------------
    def refresh_theme(self):
        stripe_table(self.tree, self.app.palette)
        for widget in self.text_widgets:
            style_text(widget, self.app.palette, self.app.fonts["body"])

    def on_show(self):
        self.check_setup()

    def check_setup(self):
        """Reload .env so a key added while the app is open is picked up."""
        self.settings = config.load()
        absent = config.missing(self.settings, self.required)
        if absent:
            self.banner_label.configure(
                text=f"{self.title} isn't set up on this computer yet. Add "
                     f"{' and '.join(absent)} to the .env file next to main.py "
                     "(see .env.example and the README), then click Check again.")
            self.banner.grid()
        else:
            self.banner.grid_remove()
        self._update_buttons()

    def _update_buttons(self):
        ready = not self.sending and not config.missing(self.settings, self.required)
        self.send_btn.state(["!disabled"] if ready else ["disabled"])
        self.delete_btn.state(["!disabled"] if self.tree.selection() else ["disabled"])

    def refresh(self):
        rows = self.db.list_messages(self.user_id, self.channel)
        fill_table(self.tree, [(r["id"], self.row_values(r)) for r in rows])
        if rows:
            self.empty_label.place_forget()
        else:
            self.empty_label.place(relx=0.5, rely=0.5, anchor="center")
        self._update_buttons()

    def confirm_and_send(self):
        try:
            recipient, values = self.collect()
        except self.error_type as exc:
            self.set_status(str(exc), "error")
            return
        if not messagebox.askyesno(f"Send {self.title}", f"Send this to {recipient}?", parent=self):
            return
        self.sending = True
        self._update_buttons()
        self.set_status("Sending...")
        settings = dict(self.settings)
        run_in_background(self.app, lambda: self.send(settings, values),
                          lambda result, error: self._sent(recipient, values, result, error))

    def _sent(self, recipient, values, result, error):
        subject, body = self.log_values(values)
        if error is None:
            self.db.add_message(self.user_id, self.channel, result, body, "sent", subject=subject)
        else:
            reason = str(error) if isinstance(error, self.error_type) else "Unexpected error."
            self.db.add_message(self.user_id, self.channel, recipient, body, "failed",
                                subject=subject, error=reason)
        if not self.winfo_exists():  # logged out while sending: the log above is enough
            return
        self.sending = False
        self.refresh()
        if error is None:
            self.clear_form()
            self.set_status(self.sent_message(result), "ok")
        else:
            self.set_status(reason, "error")

    def sent_message(self, recipient):
        return f"Sent to {recipient}."

    def delete_selected(self):
        ids = self.tree.selection()
        if not ids:
            return
        noun = "entry" if len(ids) == 1 else "entries"
        if not messagebox.askyesno("Delete history", f"Delete {len(ids)} history {noun}?", parent=self):
            return
        deleted = self.db.delete_messages(self.user_id, ids)
        self.refresh()
        self.set_status(f"Deleted {deleted} {noun}.", "ok")

    @staticmethod
    def status_text(row, sent_word):
        return sent_word if row["status"] == "sent" else f"Failed: {row['error']}"


class EmailPage(MessagePage):
    title = "Email"
    subtitle = "Send an email from your Gmail account over SMTP. One recipient per message."
    channel = "email"
    required = config.EMAIL_REQUIRED
    error_type = mailer.MailError
    columns = (
        ("created_at", "Date", 150, False),
        ("recipient", "To", 220, False),
        ("subject", "Subject", 260, False),
        ("status", "Status", 300, True),
    )

    def build_fields(self, form):
        self.to_var = tk.StringVar()
        self.subject_var = tk.StringVar()
        self.attachment = None  # (path, file_is_temporary)

        ttk.Label(form, text="To", style="CardBold.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 4))
        ttk.Label(form, text="Subject", style="CardBold.TLabel").grid(
            row=0, column=1, sticky="w", padx=(12, 0), pady=(0, 4))
        self.to_entry = ttk.Entry(form, textvariable=self.to_var)
        self.to_entry.grid(row=1, column=0, sticky="ew")
        ttk.Entry(form, textvariable=self.subject_var).grid(row=1, column=1, sticky="ew", padx=(12, 0))

        ttk.Label(form, text="Message", style="CardBold.TLabel").grid(
            row=2, column=0, sticky="w", pady=(12, 4))
        self.body = self.add_text(form, height=6)
        self.body.grid(row=3, column=0, columnspan=2, sticky="ew")

        attach_row = ttk.Frame(form, style="Plain.Card.TFrame")
        attach_row.grid(row=4, column=0, sticky="w", pady=(12, 0))
        self.attach_label = ttk.Label(attach_row, text="", style="CardMutedSmall.TLabel")
        self.attach_label.grid(row=0, column=0, padx=(0, 8))
        self.remove_attach_btn = ttk.Button(attach_row, text="Remove", width=10, command=self.remove_attachment)
        self.remove_attach_btn.grid(row=0, column=1)
        self._show_attachment()
        self.make_buttons(form, row=4)

    def _show_attachment(self):
        if self.attachment:
            self.attach_label.configure(text=f"Attachment: {os.path.basename(self.attachment[0])}")
            self.remove_attach_btn.grid()
        else:
            self.attach_label.configure(text="No attachment. Use Email CSV on the Fake Data page to attach records.")
            self.remove_attach_btn.grid_remove()

    def set_attachment(self, path, temporary):
        self.remove_attachment()
        self.attachment = (path, temporary)
        self._show_attachment()

    def remove_attachment(self):
        if self.attachment and self.attachment[1]:
            shutil.rmtree(os.path.dirname(self.attachment[0]), ignore_errors=True)
        self.attachment = None
        self._show_attachment()

    def prefill(self, subject="", body="", attachment=None):
        if subject:
            self.subject_var.set(subject)
        if body:
            set_text_value(self.body, body)
        if attachment:
            # Only files the app made in the temp folder are deleted later.
            temporary = os.path.dirname(os.path.dirname(attachment)) == tempfile.gettempdir()
            self.set_attachment(attachment, temporary)
        self.to_entry.focus_set()

    def collect(self):
        values = {
            "to": mailer.check_recipient(self.to_var.get()),
            "subject": mailer.check_subject(self.subject_var.get()),
            "body": mailer.check_body(text_value(self.body)),
            "attachment": self.attachment[0] if self.attachment else None,
        }
        return values["to"], values

    def send(self, settings, values):
        return mailer.send_email(settings, values["to"], values["subject"], values["body"],
                                 attachment_path=values["attachment"])

    def log_values(self, values):
        return values["subject"], values["body"]

    def row_values(self, row):
        return [row["created_at"], row["recipient"], one_line(row["subject"], 50),
                self.status_text(row, "Sent")]

    def clear_form(self):
        self.to_var.set("")
        self.subject_var.set("")
        set_text_value(self.body, "")
        self.remove_attachment()


class SmsPage(MessagePage):
    title = "SMS"
    subtitle = "Send a text message through the TextBee API, using the SIM in your Android phone."
    channel = "sms"
    required = config.SMS_REQUIRED
    error_type = sms_gateway.SmsError
    columns = (
        ("created_at", "Date", 150, False),
        ("recipient", "To", 150, False),
        ("body", "Message", 330, False),
        ("status", "Status", 300, True),
    )

    def build_fields(self, form):
        self.number_var = tk.StringVar()
        ttk.Label(form, text="Mobile number", style="CardBold.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 4))
        self.number_entry = ttk.Entry(form, textvariable=self.number_var)
        self.number_entry.grid(row=1, column=0, sticky="ew")
        ttk.Label(form, text="PH numbers only, e.g. 0917 123 4567", style="CardMutedSmall.TLabel").grid(
            row=1, column=1, sticky="w", padx=(12, 0))

        ttk.Label(form, text="Message", style="CardBold.TLabel").grid(row=2, column=0, sticky="w", pady=(12, 4))
        self.body = self.add_text(form, height=5)
        self.body.grid(row=3, column=0, columnspan=2, sticky="ew")
        self.body.bind("<<Modified>>", self._update_counter)

        self.counter = ttk.Label(form, text="", style="CardMutedSmall.TLabel")
        self.counter.grid(row=4, column=0, sticky="w", pady=(12, 0))
        self.make_buttons(form, row=4)
        self._update_counter()

    def _update_counter(self, _event=None):
        self.body.edit_modified(False)
        length = len(text_value(self.body).strip())
        style = "CardError.TLabel" if length > sms_gateway.MAX_LENGTH else "CardMutedSmall.TLabel"
        self.counter.configure(text=f"{length}/{sms_gateway.MAX_LENGTH} characters", style=style)

    def prefill(self, body=""):
        if body:
            set_text_value(self.body, body)
        self.number_entry.focus_set()

    def collect(self):
        number = sms_gateway.normalize_ph_mobile(self.number_var.get())
        message = sms_gateway.check_message(text_value(self.body))
        return number, {"to": number, "body": message}

    def send(self, settings, values):
        return sms_gateway.send_sms(settings, values["to"], values["body"])

    def log_values(self, values):
        return "", values["body"]

    def row_values(self, row):
        # TextBee accepting the message means the phone has it queued, not that it was delivered.
        return [row["created_at"], row["recipient"], one_line(row["body"], 50),
                self.status_text(row, "Queued on phone")]

    def sent_message(self, recipient):
        return f"Queued on your phone for {recipient}."

    def clear_form(self):
        self.number_var.set("")
        set_text_value(self.body, "")
