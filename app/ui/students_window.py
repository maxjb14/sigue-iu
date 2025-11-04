from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional

from app.services.api_client import ApiClient
from app.services.session import UserSession
from app.ui.base_window import ModuleWindow


class StudentsWindow(ModuleWindow):
    def __init__(self, master: tk.Misc, api: ApiClient, session: UserSession) -> None:
        super().__init__(master, api, session)
        self.title("Alumnos")
        self.is_admin = session.role == 'ADMIN'
        self.is_student = session.role == 'STUDENT'
        self.current_id: Optional[int] = None
        self.user_options: Dict[str, int] = {}
        self.careers: List[Dict[str, Any]] = []
        self.subjects_cache: Dict[int, List[Dict[str, Any]]] = {}
        self.current_subjects: List[int] = []

        container = ttk.Frame(self, padding=20)
        container.pack(fill=tk.BOTH, expand=True)
        container.columnconfigure(0, weight=1)

        search_frame = ttk.Frame(container)
        search_frame.grid(row=0, column=0, sticky="ew")
        ttk.Label(search_frame, text="Buscar por ID:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_var, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Buscar", command=self._search).pack(side=tk.LEFT)

        if self.is_admin:
            self._build_tree(container)

        self._build_form(container)
        self._fetch_initial_data()

        if self.is_admin:
            self._load_students()
        else:
            self._load_self()

    def _build_tree(self, container: ttk.Frame) -> None:
        columns = ('id', 'name', 'email', 'status', 'career')
        self.tree = ttk.Treeview(container, columns=columns, show='headings', height=7)
        for col in columns:
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, stretch=True)
        self.tree.grid(row=1, column=0, sticky="nsew", pady=10)
        container.rowconfigure(1, weight=1)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

    def _build_form(self, container: ttk.Frame) -> None:
        form = ttk.LabelFrame(container, text="Datos del alumno", padding=15)
        form.grid(row=2, column=0, sticky="nsew")
        form.columnconfigure(1, weight=1)

        self.id_var = tk.StringVar()
        ttk.Label(form, text="ID").grid(row=0, column=0, sticky="w", pady=5)
        self.id_entry = ttk.Entry(form, textvariable=self.id_var, state='readonly')
        self.id_entry.grid(row=0, column=1, sticky="ew", pady=5)

        ttk.Label(form, text="Email").grid(row=1, column=0, sticky="w", pady=5)
        self.email_var = tk.StringVar()
        self.email_combo = ttk.Combobox(form, textvariable=self.email_var, state='readonly')
        self.email_combo.grid(row=1, column=1, sticky="ew", pady=5)

        ttk.Label(form, text="Nombre").grid(row=2, column=0, sticky="w", pady=5)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(form, textvariable=self.name_var)
        self.name_entry.grid(row=2, column=1, sticky="ew", pady=5)

        ttk.Label(form, text="Estado").grid(row=3, column=0, sticky="w", pady=5)
        self.status_var = tk.StringVar()
        self.status_combo = ttk.Combobox(form, textvariable=self.status_var, values=['ACTIVE', 'INACTIVE'], state='readonly')
        self.status_combo.grid(row=3, column=1, sticky="ew", pady=5)

        ttk.Label(form, text="Fecha nacimiento (YYYY-MM-DD)").grid(row=4, column=0, sticky="w", pady=5)
        self.birth_var = tk.StringVar()
        self.birth_entry = ttk.Entry(form, textvariable=self.birth_var)
        self.birth_entry.grid(row=4, column=1, sticky="ew", pady=5)

        ttk.Label(form, text="Carrera").grid(row=5, column=0, sticky="w", pady=5)
        self.career_var = tk.StringVar()
        self.career_combo = ttk.Combobox(form, textvariable=self.career_var, state='readonly')
        self.career_combo.grid(row=5, column=1, sticky="ew", pady=5)
        self.career_combo.bind('<<ComboboxSelected>>', lambda _e: self._load_subjects())

        ttk.Label(form, text="Materias disponibles").grid(row=6, column=0, sticky="w", pady=(15, 5))
        self.subjects_list = tk.Listbox(form, selectmode=tk.MULTIPLE, height=8)
        self.subjects_list.grid(row=6, column=1, sticky="ew", pady=(15, 5))

        ttk.Button(form, text="Guardar", command=self._save).grid(row=7, column=0, pady=15)
        ttk.Button(form, text="Eliminar", command=self._delete).grid(row=7, column=1, pady=15)

    def _fetch_initial_data(self) -> None:
        if self.is_admin:
            users = self.api.get('/users/unassigned', params={'role': 'STUDENT', 'entity': 'students'})
            self.user_options = {f"{item['email']} ({item['username']})": item['id'] for item in users}
            self.email_combo.configure(values=list(self.user_options.keys()))
        else:
            self.email_combo.configure(state='disabled')

        self.careers = self.api.get('/careers')
        career_values = [f"{career['id']} - {career['name']}" for career in self.careers]
        self.career_combo.configure(values=career_values)
        if not self.is_admin:
            self.career_combo.configure(state='disabled')
            self.name_entry.configure(state='disabled')
            self.status_combo.configure(state='disabled')
            self.birth_entry.configure(state='disabled')

    def _load_subjects(self, career_id: Optional[int] = None) -> None:
        if career_id is None:
            selected = self.career_var.get().split(' - ')[0]
            if not selected:
                return
            career_id = int(selected)
        if career_id in self.subjects_cache:
            subjects = self.subjects_cache[career_id]
        else:
            subjects = self.api.get('/subjects', params={'careerId': career_id})
            self.subjects_cache[career_id] = subjects

        self.subjects_list.delete(0, tk.END)
        for subject in subjects:
            self.subjects_list.insert(tk.END, f"{subject['id']} - {subject['name']}")

        for index, subject in enumerate(subjects):
            if subject['id'] in self.current_subjects:
                self.subjects_list.selection_set(index)

    def _search(self) -> None:
        value = self.search_var.get().strip()
        if not value:
            messagebox.showinfo("Buscar", "Ingresa un ID")
            return
        self._load_student(int(value))

    def _on_select(self, _event: tk.Event) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        self._load_student(int(item['values'][0]))

    def _load_students(self) -> None:
        students = self.api.get('/students')
        tree = getattr(self, 'tree', None)
        if not tree:
            return
        tree.delete(*tree.get_children())
        for student in students:
            tree.insert('', tk.END, values=(student['id'], student['name'], student['email'], student['status'], student.get('career_name', '')))

    def _load_student(self, student_id: int) -> None:
        data = self.api.get(f'/students/{student_id}')
        self.current_id = student_id
        self.id_var.set(str(data['id']))
        self.name_var.set(data['name'])
        self.status_var.set(data['status'])
        self.birth_var.set(data['dateOfBirth'])
        self.current_subjects = [subject['subjectId'] for subject in data.get('subjects', [])]

        if self.is_admin:
            label = next((key for key, value in self.user_options.items() if value == data['userId']), data['email'])
            if label not in self.user_options:
                self.user_options[label] = data['userId']
                self.email_combo.configure(values=list(self.user_options.keys()))
            self.email_var.set(label)
        else:
            self.email_var.set(data['email'])

        if data.get('careerId'):
            for career in self.careers:
                if career['id'] == data['careerId']:
                    self.career_var.set(f"{career['id']} - {career['name']}")
                    break
            self._load_subjects(data['careerId'])
        else:
            self.subjects_list.delete(0, tk.END)

    def _load_self(self) -> None:
        try:
            data = self.api.get('/students/me')
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Error", str(error))
            return
        self._load_student(data['id'])

    def _collect_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}

        selected_subjects = [self.subjects_list.get(i) for i in self.subjects_list.curselection()]
        subjects_ids = [int(text.split(' - ')[0]) for text in selected_subjects]
        payload['subjects'] = subjects_ids

        if self.is_admin:
            email_label = self.email_var.get()
            user_id = self.user_options.get(email_label)
            if not user_id:
                raise ValueError('Selecciona un correo válido')
            payload['userId'] = user_id

            name = self.name_var.get().strip()
            status = self.status_var.get().strip()
            dob = self.birth_var.get().strip()
            career_value = self.career_var.get().strip()

            if not name or not status or not dob or not career_value:
                raise ValueError('Todos los campos son requeridos')

            payload['name'] = name
            payload['status'] = status
            payload['dateOfBirth'] = dob
            payload['careerId'] = int(career_value.split(' - ')[0])
        else:
            if self.current_id is None:
                raise ValueError('No hay alumno cargado')

        return payload

    def _save(self) -> None:
        try:
            payload = self._collect_payload()
        except ValueError as error:
            messagebox.showwarning("Validación", str(error))
            return

        try:
            if self.current_id is None:
                response = self.api.post('/students', payload)
            else:
                response = self.api.put(f"/students/{self.current_id}", payload)
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Error", str(error))
            return

        messagebox.showinfo("Éxito", "Alumno guardado")
        if self.is_admin:
            self._fetch_initial_data()
        self._load_student(response['id'])
        if self.is_admin:
            self._load_students()

    def _delete(self) -> None:
        if not self.is_admin:
            messagebox.showwarning("Permiso", "Solo el administrador puede eliminar alumnos")
            return
        if self.current_id is None:
            messagebox.showinfo("Operación", "Selecciona un alumno")
            return
        if not messagebox.askyesno("Eliminar", "¿Deseas eliminar al alumno?"):
            return
        try:
            self.api.delete(f"/students/{self.current_id}")
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Error", str(error))
            return
        messagebox.showinfo("Éxito", "Alumno eliminado")
        self.current_id = None
        if self.is_admin:
            self._fetch_initial_data()
        self._load_students()
