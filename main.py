"""Fake Data Generator: ITL313-18 (SIA 2 Lab) mini project.

Run:  python main.py
"""
import tkinter as tk

from app.db import Database
from app.ui import theme
from app.ui.dashboard import DashboardFrame
from app.ui.login import LoginFrame


class App(tk.Tk):
    def __init__(self, db_path=None):
        super().__init__()
        self.title("Fake Data Generator")
        self.db = Database(db_path) if db_path else Database()
        self.user = None
        self.theme = "light"
        self.fonts = theme.setup_fonts(self)
        self.palette = theme.apply_theme(self, self.theme, self.fonts)
        self._icon = theme.make_icon(self)
        self.iconphoto(True, self._icon)

        self.geometry("1180x700")
        self.minsize(560, 640)
        self.screen = None
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.show_login()

    def _swap(self, frame):
        if self.screen is not None:
            self.screen.destroy()
        self.screen = frame
        frame.pack(fill="both", expand=True)

    def show_login(self, message="", ok=True, username=""):
        self.minsize(560, 640)
        self._swap(LoginFrame(self, self, message=message, message_ok=ok, username=username))

    def on_login(self, user):
        self.user = {"id": user["id"], "username": user["username"]}
        self.set_theme(user["theme"], save=False)
        self.minsize(980, 560)
        self._swap(DashboardFrame(self, self, self.user))

    def logout(self):
        self.user = None
        self.show_login("You've been logged out.", ok=True)

    def set_theme(self, name, save=True):
        self.theme = name
        self.palette = theme.apply_theme(self, name, self.fonts)
        if save and self.user:
            self.db.set_theme(self.user["id"], name)
        if self.screen is not None:
            if hasattr(self.screen, "refresh_theme"):
                self.screen.refresh_theme()
            if hasattr(self.screen, "refresh_theme_button"):
                self.screen.refresh_theme_button()

    def toggle_theme(self):
        self.set_theme("light" if self.theme == "dark" else "dark")

    def close(self):
        self.db.close()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
