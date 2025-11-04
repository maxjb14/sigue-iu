from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional

from app.services.api_client import ApiClient
from app.services.session import UserSession
from app.ui.base_window import ModuleWindow


class SchedulesWindow(ModuleWindow):
    def __init__(self, master: tk.Misc, api: ApiClient, session: UserSession) -> None:
        super().__init__(master, api, session)
        self.title("Horarios")
        self.current_id: Optional[int] = None

        container = ttk.Frame(self, padding=20)
        container.pack(fill=tk.BOTH, expand=True)
        container.columnconfigure(0, weight=1)

        self._build_tree(container)
        self._build_form(container)
        self._load_schedules()

    def _build_tree(self, container: ttk.Frame) -> None:
        columns = ('id', 'shift', 'time')
        self.tree = ttk.Treeview(container, columns=columns, show='headings', height=8)
        for col in columns:
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, stretch=True)
        self.tree.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        container.rowconfigure(0, weight=1)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

    def _build_form(self, container: ttk.Frame) -> None:
        form = ttk.LabelFrame(container, text="Datos del horario", padding=15)
        form.grid(row=1, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)

        self.id_var = tk.StringVar()
        ttk.Label(form, text="ID").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.id_var, state='readonly').grid(row=0, column=1, sticky="ew", pady=5)

        self.time_var = tk.StringVar()
        ttk.Label(form, text="Hora (HH:MM)").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.time_var).grid(row=1, column=1, sticky="ew", pady=5)

        self.shift_var = tk.StringVar()
        ttk.Label(form, text="Turno").grid(row=2, column=0, sticky="w", pady=5)
        self.shift_combo = ttk.Combobox(form, textvariable=self.shift_var, values=['MATUTINO', 'VESPERTINO'], state='readonly')
        self.shift_combo.grid(row=2, column=1, sticky="ew", pady=5)

        buttons = ttk.Frame(form)
        buttons.grid(row=3, column=0, columnspan=2, pady=15)
        ttk.Button(buttons, text="Nuevo", command=self._reset).grid(row=0, column=0, padx=5)
        ttk.Button(buttons, text="Guardar", command=self._save).grid(row=0, column=1, padx=5)
        ttk.Button(buttons, text="Eliminar", command=self._delete).grid(row=0, column=2, padx=5)

    def _reset(self) -> None:
        self.current_id = None
        self.id_var.set('')
        self.time_var.set('')
        self.shift_var.set('')

    def _on_select(self, _event: tk.Event) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        self.current_id = int(item['values'][0])
        self.id_var.set(str(item['values'][0]))
        self.shift_var.set(item['values'][1])
        self.time_var.set(item['values'][2])

    def _collect_payload(self) -> Dict[str, str]:
        time_value = self.time_var.get().strip()
        shift = self.shift_var.get().strip()
        if not time_value:
            raise ValueError('La hora es requerida')
        if not shift:
            hour = int(time_value.split(':')[0])
            shift = 'MATUTINO' if hour < 12 else 'VESPERTINO'
        return {'time': time_value, 'shift': shift}

    def _save(self) -> None:
        try:
            payload = self._collect_payload()
        except ValueError as error:
            messagebox.showwarning("Validación", str(error))
            return
        try:
            if self.current_id is None:
                schedule = self.api.post('/schedules', payload)
            else:
                schedule = self.api.put(f"/schedules/{self.current_id}", payload)
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Error", str(error))
            return
        messagebox.showinfo("Éxito", "Horario guardado")
        self.current_id = schedule['id']
        self.id_var.set(str(schedule['id']))
        self._load_schedules()

    def _delete(self) -> None:
        if self.current_id is None:
            messagebox.showinfo("Operación", "Selecciona un horario")
            return
        if not messagebox.askyesno("Eliminar", "¿Deseas eliminar el horario?"):
            return
        try:
            self.api.delete(f"/schedules/{self.current_id}")
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Error", str(error))
            return
        messagebox.showinfo("Éxito", "Horario eliminado")
        self._reset()
        self._load_schedules()

    def _load_schedules(self) -> None:
        schedules = self.api.get('/schedules')
        self.tree.delete(*self.tree.get_children())
        for schedule in schedules:
            self.tree.insert('', tk.END, values=(schedule['id'], schedule['shift'], schedule['time']))
