from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional

from app.services.api_client import ApiClient
from app.services.session import UserSession
from app.ui.base_window import ModuleWindow


class TeachersWindow(ModuleWindow):
    def __init__(self, master: tk.Misc, api: ApiClient, session: UserSession) -> None:
        super().__init__(master, api, session)
        self.title("Maestros")
        self.is_admin = session.role == 'ADMIN'
        self.current_id: Optional[int] = None
        self.user_options: Dict[str, int] = {}
        self.careers: List[Dict[str, Any]] = []
        self.subjects: List[Dict[str, Any]] = []
        self.current_subjects: List[int] = []

        container = ttk.Frame(self, padding=20)
        container.pack(fill=tk.BOTH, expand=True)
        container.columnconfigure(0, weight=1)

        if self.is_admin:
            self._build_tree(container)

        self._build_form(container)
        self._fetch_support_data()

        if self.is_admin:
            self._load_teachers()
        else:
            self._load_self()

    def _build_tree(self, container: ttk.Frame) -> None:
        columns = ('id', 'name', 'email', 'degree')
        self.tree = ttk.Treeview(container, columns=columns, show='headings', height=7)
        for col in columns:
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, stretch=True)
        self.tree.grid(row=0, column=0, sticky="nsew", pady=10)
        container.rowconfigure(0, weight=1)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

    def _build_form(self, container: ttk.Frame) -> None:
        form = ttk.LabelFrame(container, text="Datos del maestro", padding=15)
        form.grid(row=1, column=0, sticky="nsew")
        form.columnconfigure(1, weight=1)

        self.id_var = tk.StringVar()
        ttk.Label(form, text="ID").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.id_var, state='readonly').grid(row=0, column=1, sticky="ew", pady=5)

        ttk.Label(form, text="Email").grid(row=1, column=0, sticky="w", pady=5)
        self.email_var = tk.StringVar()
        self.email_combo = ttk.Combobox(form, textvariable=self.email_var, state='readonly')
        self.email_combo.grid(row=1, column=1, sticky="ew", pady=5)

        ttk.Label(form, text="Nombre").grid(row=2, column=0, sticky="w", pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.name_var).grid(row=2, column=1, sticky="ew", pady=5)

        ttk.Label(form, text="Grado de estudios").grid(row=3, column=0, sticky="w", pady=5)
        self.degree_var = tk.StringVar()
        self.degree_combo = ttk.Combobox(form, textvariable=self.degree_var, values=['LICENCIATURA', 'MAESTRIA', 'DOCTORADO'], state='readonly')
        self.degree_combo.grid(row=3, column=1, sticky="ew", pady=5)

        ttk.Label(form, text="Carreras asignadas").grid(row=4, column=0, sticky="w", pady=(15, 5))
        self.careers_list = tk.Listbox(form, selectmode=tk.MULTIPLE, height=6)
        self.careers_list.grid(row=4, column=1, sticky="ew", pady=(15, 5))
        self.careers_list.bind('<<ListboxSelect>>', lambda _e: self._refresh_subject_list())

        ttk.Label(form, text="Materias que imparte").grid(row=5, column=0, sticky="w", pady=(15, 5))
        self.subjects_list = tk.Listbox(form, selectmode=tk.MULTIPLE, height=8)
        self.subjects_list.grid(row=5, column=1, sticky="ew", pady=(15, 5))
        self.subjects_list.bind('<<ListboxSelect>>', lambda _e: self._update_selected_subjects())

        buttons = ttk.Frame(form)
        buttons.grid(row=6, column=0, columnspan=2, pady=15)
        ttk.Button(buttons, text="Nuevo", command=self._reset).grid(row=0, column=0, padx=5)
        ttk.Button(buttons, text="Guardar", command=self._save).grid(row=0, column=1, padx=5)
        ttk.Button(buttons, text="Eliminar", command=self._delete).grid(row=0, column=2, padx=5)

        if not self.is_admin:
            self.email_combo.configure(state='disabled')
            self.careers_list.configure(state='disabled')
            self.subjects_list.configure(state='disabled')

    def _fetch_support_data(self) -> None:
        if self.is_admin:
            users = self.api.get('/users/unassigned', params={'role': 'TEACHER', 'entity': 'teachers'})
            self.user_options = {f"{item['email']} ({item['username']})": item['id'] for item in users}
            self.email_combo.configure(values=list(self.user_options.keys()))

        self.careers = self.api.get('/careers')
        self._refresh_career_list()

        self.subjects = self.api.get('/subjects')
        self._refresh_subject_list()

    def _refresh_career_list(self) -> None:
        self.careers_list.delete(0, tk.END)
        for career in self.careers:
            self.careers_list.insert(tk.END, f"{career['id']} - {career['name']}")

    def _refresh_subject_list(self) -> None:
        selected_careers = {int(self.careers_list.get(i).split(' - ')[0]) for i in self.careers_list.curselection()}
        self.subjects_list.delete(0, tk.END)
        for subject in self.subjects:
            if not selected_careers or subject['careerId'] in selected_careers:
                label = f"{subject['id']} - {subject['name']} ({subject.get('careerName', '')})"
                self.subjects_list.insert(tk.END, label)
        # Restaurar selección previa
        for index in range(self.subjects_list.size()):
            subject_id = int(self.subjects_list.get(index).split(' - ')[0])
            if hasattr(self, 'current_subjects') and subject_id in getattr(self, 'current_subjects'):
                self.subjects_list.selection_set(index)
        self._update_selected_subjects()

    def _load_teachers(self) -> None:
        teachers = self.api.get('/teachers')
        self.tree.delete(*self.tree.get_children())
        for teacher in teachers:
            self.tree.insert('', tk.END, values=(teacher['id'], teacher['name'], teacher['email'], teacher['degree']))

    def _on_select(self, _event: tk.Event) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        self._load_teacher(int(item['values'][0]))

    def _load_teacher(self, teacher_id: int) -> None:
        data = self.api.get(f'/teachers/{teacher_id}')
        self.current_id = teacher_id
        self.id_var.set(str(data['id']))
        self.name_var.set(data['name'])
        self.degree_var.set(data['degree'])
        self.current_subjects = [subject['subjectId'] for subject in data.get('subjects', [])]

        if self.is_admin:
            label = next((key for key, value in self.user_options.items() if value == data['user_id']), data['email'])
            if label not in self.user_options:
                self.user_options[label] = data['user_id']
                self.email_combo.configure(values=list(self.user_options.keys()))
            self.email_var.set(label)
        else:
            self.email_var.set(data['email'])

        career_ids = [career['careerId'] for career in data.get('careers', [])]
        self.careers_list.selection_clear(0, tk.END)
        for index in range(self.careers_list.size()):
            career_id = int(self.careers_list.get(index).split(' - ')[0])
            if career_id in career_ids:
                self.careers_list.selection_set(index)
        self._refresh_subject_list()

    def _update_selected_subjects(self) -> None:
        self.current_subjects = [
            int(self.subjects_list.get(i).split(' - ')[0]) for i in self.subjects_list.curselection()
        ]

    def _load_self(self) -> None:
        try:
            data = self.api.get('/teachers/me')
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Error", str(error))
            return
        self._load_teacher(data['id'])

    def _collect_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            'name': self.name_var.get().strip(),
            'degree': self.degree_var.get().strip() or None
        }

        if not payload['name'] or not payload['degree']:
            raise ValueError('Nombre y grado son requeridos')

        if self.is_admin:
            email_label = self.email_var.get()
            user_id = self.user_options.get(email_label)
            if self.current_id is None and not user_id:
                raise ValueError('Selecciona un correo de usuario disponible')
            if user_id:
                payload['userId'] = user_id

            career_ids = [int(self.careers_list.get(i).split(' - ')[0]) for i in self.careers_list.curselection()]
            payload['careerIds'] = career_ids
            subject_ids = [int(self.subjects_list.get(i).split(' - ')[0]) for i in self.subjects_list.curselection()]
            payload['subjectIds'] = subject_ids

        return payload

    def _save(self) -> None:
        try:
            payload = self._collect_payload()
        except ValueError as error:
            messagebox.showwarning("Validación", str(error))
            return

        try:
            if self.current_id is None:
                response = self.api.post('/teachers', payload)
            else:
                response = self.api.put(f"/teachers/{self.current_id}", payload)
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Error", str(error))
            return

        messagebox.showinfo("Éxito", "Maestro guardado")
        if self.is_admin:
            self._fetch_support_data()
        self._load_teacher(response['id'])
        if self.is_admin:
            self._load_teachers()

    def _delete(self) -> None:
        if not self.is_admin:
            messagebox.showwarning("Permiso", "Solo el administrador puede eliminar maestros")
            return
        if self.current_id is None:
            messagebox.showinfo("Operación", "Selecciona un maestro")
            return
        if not messagebox.askyesno("Eliminar", "¿Deseas eliminar el maestro?"):
            return
        try:
            self.api.delete(f"/teachers/{self.current_id}")
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Error", str(error))
            return
        messagebox.showinfo("Éxito", "Maestro eliminado")
        self._reset()
        if self.is_admin:
            self._fetch_support_data()
        self._load_teachers()

    def _reset(self) -> None:
        self.current_id = None
        self.id_var.set('')
        self.name_var.set('')
        self.degree_var.set('')
        self.email_var.set('')
        self.careers_list.selection_clear(0, tk.END)
        self.subjects_list.selection_clear(0, tk.END)
        self.current_subjects = []
