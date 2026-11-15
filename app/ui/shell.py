"""The main window after login: a sidebar on the left, the chosen tool on the right."""
from tkinter import ttk

from app.ui.fakedata_page import FakeDataPage
from app.ui.links_page import LinksPage
from app.ui.message_pages import EmailPage, SmsPage

TOOLS = (
    ("fake", "Fake Data", FakeDataPage),
    ("links", "URL Shortener", LinksPage),
    ("email", "Email", EmailPage),
    ("sms", "SMS", SmsPage),
)


class ShellFrame(ttk.Frame):
    def __init__(self, master, app, user):
        super().__init__(master)
        self.app = app
        self.user = user
        self.current = None
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)

        side = ttk.Frame(self, style="Sidebar.TFrame", padding=(16, 20), width=220)
        side.grid(row=0, column=0, sticky="ns")
        side.grid_propagate(False)
        side.columnconfigure(0, weight=1)
        ttk.Label(side, text="Utility Hub", style="SidebarTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(side, text=f"Signed in as {user['username']}", style="Sidebar.TLabel").grid(
            row=1, column=0, sticky="w", pady=(2, 20))

        self.nav = {}
        for row, (key, label, _page) in enumerate(TOOLS, start=2):
            button = ttk.Button(side, text=label, style="Nav.TButton", command=lambda k=key: self.show(k))
            button.grid(row=row, column=0, sticky="ew", pady=2)
            self.nav[key] = button

        side.rowconfigure(len(TOOLS) + 2, weight=1)  # pushes the two buttons below to the bottom
        self.theme_btn = ttk.Button(side, command=app.toggle_theme)
        self.theme_btn.grid(row=len(TOOLS) + 3, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(side, text="Log out", command=app.logout).grid(row=len(TOOLS) + 4, column=0, sticky="ew")

        ttk.Separator(self, orient="vertical").grid(row=0, column=1, sticky="ns")

        content = ttk.Frame(self)
        content.grid(row=0, column=2, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)
        self.pages = {}
        for key, _label, page_class in TOOLS:
            page = page_class(content, self)
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[key] = page

        self.refresh_theme()
        self.show("fake")

    def show(self, key):
        self.current = key
        for nav_key, button in self.nav.items():
            button.configure(style="NavActive.TButton" if nav_key == key else "Nav.TButton")
        self.pages[key].tkraise()
        self.pages[key].on_show()

    def compose_email(self, subject="", body="", attachment=None):
        self.show("email")
        self.pages["email"].prefill(subject=subject, body=body, attachment=attachment)

    def compose_sms(self, body=""):
        self.show("sms")
        self.pages["sms"].prefill(body=body)

    def refresh_theme(self):
        self.theme_btn.configure(text="Light mode" if self.app.theme == "dark" else "Dark mode")
        for page in self.pages.values():
            page.refresh_theme()

    def destroy(self):
        # Don't leave a temporary CSV behind when the user logs out.
        self.pages["email"].remove_attachment()
        super().destroy()
