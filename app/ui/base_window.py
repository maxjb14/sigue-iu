from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Protocol

from app.services.api_client import ApiClient, ApiError
from app.services.session import UserSession


class SupportsRefresh(Protocol):
    def refresh(self) -> None:  # pragma: no cover - protocolo para refrescos opcionales
        ...


class ModuleWindow(tk.Toplevel):
    def __init__(self, master: tk.Misc, api: ApiClient, session: UserSession) -> None:
        super().__init__(master)
        self.api = api
        self.session = session
        self.geometry('700x600')
        self.minsize(600, 500)

    def handle_api_call(self, func, *args, **kwargs):  # type: ignore[no-untyped-def]
        try:
            return func(*args, **kwargs)
        except ApiError as error:
            messagebox.showerror("Error", error.message)
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Error", str(error))
        return None
