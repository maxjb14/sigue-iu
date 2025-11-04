from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, Optional

from app.services.api_client import ApiClient
from app.services.session import UserSession
from app.ui.base_window import ModuleWindow


class UsersWindow(ModuleWindow):
    def __init__(self, master: tk.Misc, api: ApiClient, session: UserSession) -> None:
        super().__init__(master, api, session)
        self.title("Usuarios")
        self.is_admin = session.role == 'ADMIN'
        self.current_user_id: Optional[int] = None

        container = ttk.Frame(self, padding=20)
        container.pack(fill=tk.BOTH, expand=True)
        container.columnconfigure(1, weight=1)

        # Búsqueda por ID
        ttk.Label(container, text="Buscar por ID:").grid(row=0, column=0, sticky="w")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(container, textvariable=self.search_var, width=15)
        search_entry.grid(row=0, column=1, sticky="w")
        ttk.Button(container, text="Buscar", command=self._search_by_id).grid(row=0, column=2, padx=5)

        if self.is_admin:
            self._build_tree(container)

        self._build_form(container)
        self._set_default_state()

        if self.is_admin:
            self._load_users()
        else:
            self._load_self()

    def _build_tree(self, container: ttk.Frame) -> None:
        columns = ("id", "email", "username", "role")
        self.tree = ttk.Treeview(container, columns=columns, show='headings', height=8)
        for col in columns:
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, stretch=True)
        self.tree.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=10)
        container.rowconfigure(1, weight=1)
        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)

    def _build_form(self, container: ttk.Frame) -> None:
        form = ttk.LabelFrame(container, text="Datos del usuario", padding=15)
        form.grid(row=2, column=0, columnspan=3, pady=10, sticky="ew")
        form.columnconfigure(1, weight=1)

        self.id_var = tk.StringVar()
        ttk.Label(form, text="ID").grid(row=0, column=0, sticky="w", pady=5)
        self.id_entry = ttk.Entry(form, textvariable=self.id_var, state='readonly')
        self.id_entry.grid(row=0, column=1, sticky="ew", pady=5)

        self.email_var = tk.StringVar()
        ttk.Label(form, text="Email").grid(row=1, column=0, sticky="w", pady=5)
        self.email_entry = ttk.Entry(form, textvariable=self.email_var)
        self.email_entry.grid(row=1, column=1, sticky="ew", pady=5)

        self.username_var = tk.StringVar()
        ttk.Label(form, text="Nombre de usuario").grid(row=2, column=0, sticky="w", pady=5)
        self.username_entry = ttk.Entry(form, textvariable=self.username_var)
        self.username_entry.grid(row=2, column=1, sticky="ew", pady=5)

        self.password_var = tk.StringVar()
        ttk.Label(form, text="Contraseña").grid(row=3, column=0, sticky="w", pady=5)
        self.password_entry = ttk.Entry(form, textvariable=self.password_var, show='*')
        self.password_entry.grid(row=3, column=1, sticky="ew", pady=5)

        ttk.Label(form, text="Perfil").grid(row=4, column=0, sticky="w", pady=5)
        self.role_var = tk.StringVar()
        self.role_combo = ttk.Combobox(form, textvariable=self.role_var, values=['ADMIN', 'TEACHER', 'STUDENT'], state='readonly')
        self.role_combo.grid(row=4, column=1, sticky="ew", pady=5)

        buttons = ttk.Frame(form)
        buttons.grid(row=5, column=0, columnspan=2, pady=(15, 0))

        ttk.Button(buttons, text="Nuevo", command=self._set_default_state).grid(row=0, column=0, padx=5)
        ttk.Button(buttons, text="Guardar", command=self._save_user).grid(row=0, column=1, padx=5)
        ttk.Button(buttons, text="Eliminar", command=self._delete_user).grid(row=0, column=2, padx=5)

    def _set_default_state(self) -> None:
        self.current_user_id = None
        self.id_var.set('')
        self.email_var.set('')
        self.username_var.set('')
        self.password_var.set('')
        self.role_var.set('ADMIN' if self.is_admin else self.session.role or '')

        is_admin = self.is_admin
        state_email = 'normal' if is_admin else 'readonly'
        state_role = 'readonly' if is_admin else 'disabled'

        self.email_entry.configure(state=state_email)
        self.role_combo.configure(state=state_role)

    def _search_by_id(self) -> None:
        value = self.search_var.get().strip()
        if not value:
            messagebox.showinfo("Buscar", "Ingresa un ID para buscar")
            return
        try:
            user = self.api.get(f"/users/{value}")
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Error", str(error))
            return
        self._fill_form(user)

    def _on_tree_select(self, _event: tk.Event) -> None:
        if not self.is_admin:
            return
        selection = getattr(self, 'tree', None).selection()  # type: ignore[attr-defined]
        if not selection:
            return
        item = getattr(self, 'tree', None).item(selection[0])  # type: ignore[attr-defined]
        user_id = item['values'][0]
        try:
            user = self.api.get(f"/users/{user_id}")
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Error", str(error))
            return
        self._fill_form(user)

    def _fill_form(self, user: Dict[str, Any]) -> None:
        self.current_user_id = int(user.get('id'))
        self.id_var.set(str(user.get('id', '')))
        self.email_var.set(user.get('email', ''))
        self.username_var.set(user.get('username', ''))
        self.role_var.set(user.get('role', ''))
        self.password_var.set('')

        self.email_entry.configure(state='normal' if self.is_admin else 'readonly')

    def _collect_payload(self) -> Dict[str, Any]:
        email = self.email_var.get().strip()
        username = self.username_var.get().strip()
        password = self.password_var.get().strip() or None
        role = self.role_var.get().strip() or None

        payload: Dict[str, Any] = {}

        if self.current_user_id is None:
            if not email or not username or not password or not role:
                raise ValueError('Todos los campos son requeridos para crear usuario')
            payload = {
                'email': email,
                'username': username,
                'password': password,
                'role': role
            }
        else:
            if self.is_admin and email:
                payload['email'] = email
            if username:
                payload['username'] = username
            if password:
                payload['password'] = password
            if self.is_admin and role:
                payload['role'] = role
        return payload

    def _save_user(self) -> None:
        try:
            payload = self._collect_payload()
        except ValueError as error:
            messagebox.showwarning("Validación", str(error))
            return

        try:
            if self.current_user_id is None:
                user = self.api.post('/users', payload)
            else:
                user = self.api.put(f"/users/{self.current_user_id}", payload)
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Error", str(error))
            return

        messagebox.showinfo("Éxito", "Usuario guardado correctamente")
        self._fill_form(user)
        if self.is_admin:
            self._load_users()

    def _delete_user(self) -> None:
        if not self.is_admin:
            messagebox.showwarning("Permiso", "Solo el administrador puede eliminar usuarios")
            return
        if self.current_user_id is None:
            messagebox.showinfo("Eliminar", "Selecciona un usuario")
            return
        if not messagebox.askyesno("Eliminar", "¿Deseas eliminar el usuario?"):
            return
        try:
            self.api.delete(f"/users/{self.current_user_id}")
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Error", str(error))
            return
        messagebox.showinfo("Éxito", "Usuario eliminado")
        self._set_default_state()
        if self.is_admin:
            self._load_users()

    def _load_users(self) -> None:
        if not self.is_admin:
            return
        try:
            users = self.api.get('/users')
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Error", str(error))
            return
        tree = getattr(self, 'tree', None)
        if not tree:
            return
        tree.delete(*tree.get_children())
        for user in users:
            tree.insert('', tk.END, values=(user['id'], user['email'], user['username'], user['role']))

    def _load_self(self) -> None:
        self.current_user_id = self.session.user.get('id')  # type: ignore[assignment]
        if not self.current_user_id:
            return
        try:
            user = self.api.get(f"/users/{self.current_user_id}")
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Error", str(error))
            return
        self._fill_form(user)
        self.email_entry.configure(state='readonly')
        self.role_combo.configure(state='disabled')
