"""Login and register screen."""
import tkinter as tk
from tkinter import ttk

from app import auth


class LoginFrame(ttk.Frame):
    def __init__(self, master, app, message="", message_ok=True, username=""):
        super().__init__(master, padding=24)
        self.app = app
        self.mode = "login"

        self.username = tk.StringVar(value=username)
        self.password = tk.StringVar()
        self.confirm = tk.StringVar()
        self.show_pw = tk.BooleanVar(value=False)

        # Center the card in the window, whatever its size.
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        card = ttk.Frame(self, style="Card.TFrame", padding=(36, 32))
        card.grid(row=0, column=0)
        card.columnconfigure((0, 1), weight=1, uniform="half")
        self.card = card

        ttk.Label(card, text="Fake Data Generator", style="CardTitle.TLabel").grid(
            row=0, column=0, columnspan=2)
        ttk.Label(card, text="Philippine sample records for testing", style="CardMuted.TLabel").grid(
            row=1, column=0, columnspan=2, pady=(2, 20))

        # Equal-width segmented switch: Log in | Register
        self.login_tab = ttk.Button(card, text="Log in", command=lambda: self.set_mode("login"))
        self.register_tab = ttk.Button(card, text="Register", command=lambda: self.set_mode("register"))
        self.login_tab.grid(row=2, column=0, sticky="ew", padx=(0, 4))
        self.register_tab.grid(row=2, column=1, sticky="ew", padx=(4, 0))

        self.user_entry = self._field(card, 3, "Username", self.username)
        self.pw_entry = self._field(card, 5, "Password", self.password, secret=True)
        self.confirm_label, self.confirm_entry = self._field(
            card, 7, "Confirm password", self.confirm, secret=True, return_label=True)

        ttk.Checkbutton(card, text="Show password", variable=self.show_pw, style="Card.TCheckbutton",
                        command=self._toggle_show).grid(row=9, column=0, columnspan=2, sticky="w", pady=(8, 0))

        self.hint = ttk.Label(card, text="", style="CardMuted.TLabel", wraplength=320, justify="center")
        self.hint.grid(row=10, column=0, columnspan=2, pady=(8, 0))

        self.submit_btn = ttk.Button(card, text="Log in", style="Accent.TButton", command=self.submit)
        self.submit_btn.grid(row=11, column=0, columnspan=2, sticky="ew", pady=(14, 0))

        self.message = ttk.Label(card, text="", style="CardError.TLabel", wraplength=320, justify="center")
        self.message.grid(row=12, column=0, columnspan=2, pady=(12, 0))

        self.theme_btn = ttk.Button(card, command=app.toggle_theme)
        self.theme_btn.grid(row=13, column=0, columnspan=2, pady=(16, 0))

        for entry in (self.user_entry, self.pw_entry, self.confirm_entry):
            entry.bind("<Return>", lambda _e: self.submit())

        self.set_mode("login")
        self.refresh_theme_button()
        if message:
            self.show_message(message, ok=message_ok)
        (self.pw_entry if username else self.user_entry).focus_set()

    def _field(self, card, row, label, var, secret=False, return_label=False):
        lbl = ttk.Label(card, text=label, style="CardBold.TLabel")
        lbl.grid(row=row, column=0, columnspan=2, sticky="w", pady=(14, 4))
        entry = ttk.Entry(card, textvariable=var, width=36, show="•" if secret else "")
        entry.grid(row=row + 1, column=0, columnspan=2, sticky="ew")
        return (lbl, entry) if return_label else entry

    def _toggle_show(self):
        char = "" if self.show_pw.get() else "•"
        self.pw_entry.configure(show=char)
        self.confirm_entry.configure(show=char)

    def set_mode(self, mode):
        self.mode = mode
        is_reg = mode == "register"
        self.login_tab.configure(style="TButton" if is_reg else "Accent.TButton")
        self.register_tab.configure(style="Accent.TButton" if is_reg else "TButton")
        self.submit_btn.configure(text="Create account" if is_reg else "Log in")
        if is_reg:
            self.confirm_label.grid()
            self.confirm_entry.grid()
            self.hint.configure(text="Username: 3-20 letters, numbers or _.  "
                                     "Password: 8+ characters with a letter and a number.")
            self.hint.grid()
        else:
            self.confirm_label.grid_remove()
            self.confirm_entry.grid_remove()
            self.hint.grid_remove()
        self.password.set("")
        self.confirm.set("")
        self.show_message("")

    def show_message(self, text, ok=False):
        self.message.configure(text=text, style="CardSuccess.TLabel" if ok else "CardError.TLabel")

    def refresh_theme_button(self):
        self.theme_btn.configure(text="Switch to light mode" if self.app.theme == "dark" else "Switch to dark mode")

    def submit(self):
        self.submit_btn.state(["disabled"])
        self.configure(cursor="watch")
        self.update_idletasks()
        try:
            if self.mode == "register":
                auth.register(self.app.db, self.username.get(), self.password.get(), self.confirm.get())
                name = self.username.get().strip()
                self.set_mode("login")
                self.username.set(name)
                self.show_message("Account created. You can log in now.", ok=True)
                self.pw_entry.focus_set()
            else:
                user = auth.login(self.app.db, self.username.get(), self.password.get())
                self.password.set("")
                self.app.on_login(user)
                return  # this frame is gone now
        except auth.AuthError as exc:
            self.password.set("")
            self.confirm.set("")
            self.show_message(str(exc))
            self.pw_entry.focus_set()
        finally:
            if self.winfo_exists():
                self.submit_btn.state(["!disabled"])
                self.configure(cursor="")
