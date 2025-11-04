from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional

from app.services.api_client import ApiClient
from app.services.session import UserSession
from app.ui.base_window import ModuleWindow


class GroupsWindow(ModuleWindow):
    def __init__(self, master: tk.Misc, api: ApiClient, session: UserSession) -> None:
        super().__init__(master, api, session)
        self.title("Grupos")
        self.current_id: Optional[int] = None
        self.careers: List[Dict[str, Any]] = []
        self.subjects_by_career: Dict[int, List[Dict[str, Any]]] = {}
        self.teachers: List[Dict[str, Any]] = []
        self.classrooms: List[Dict[str, Any]] = []
        self.schedules: List[Dict[str, Any]] = []

        container = ttk.Frame(self, padding=20)
        container.pack(fill=tk.BOTH, expand=True)
        container.columnconfigure(0, weight=1)

        self._build_tree(container)
        self._build_form(container)
        self._fetch_support_data()
        self._load_groups()

    def _build_tree(self, container: ttk.Frame) -> None:
        columns = ('id', 'name', 'career', 'subject', 'teacher', 'schedule')
        self.tree = ttk.Treeview(container, columns=columns, show='headings', height=7)
        headers = {
            'id': 'ID',
            'name': 'Grupo',
            'career': 'Carrera',
            'subject': 'Materia',
            'teacher': 'Maestro',
            'schedule': 'Horario'
        }
        for col in columns:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, stretch=True)
        self.tree.grid(row=0, column=0, sticky="nsew", pady=10)
        container.rowconfigure(0, weight=1)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

    def _build_form(self, container: ttk.Frame) -> None:
        form = ttk.LabelFrame(container, text="Datos del grupo", padding=15)
        form.grid(row=1, column=0, sticky="nsew")
        form.columnconfigure(1, weight=1)

        self.id_var = tk.StringVar()
        ttk.Label(form, text="ID").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.id_var, state='readonly').grid(row=0, column=1, sticky="ew", pady=5)

        self.name_var = tk.StringVar()
        ttk.Label(form, text="Nombre de grupo").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.name_var).grid(row=1, column=1, sticky="ew", pady=5)

        self.career_var = tk.StringVar()
        ttk.Label(form, text="Carrera").grid(row=2, column=0, sticky="w", pady=5)
        self.career_combo = ttk.Combobox(form, textvariable=self.career_var, state='readonly')
        self.career_combo.grid(row=2, column=1, sticky="ew", pady=5)
        self.career_combo.bind('<<ComboboxSelected>>', lambda _e: self._refresh_subject_combo())

        self.subject_var = tk.StringVar()
        ttk.Label(form, text="Materia").grid(row=3, column=0, sticky="w", pady=5)
        self.subject_combo = ttk.Combobox(form, textvariable=self.subject_var, state='readonly')
        self.subject_combo.grid(row=3, column=1, sticky="ew", pady=5)

        self.teacher_var = tk.StringVar()
        ttk.Label(form, text="Maestro").grid(row=4, column=0, sticky="w", pady=5)
        self.teacher_combo = ttk.Combobox(form, textvariable=self.teacher_var, state='readonly')
        self.teacher_combo.grid(row=4, column=1, sticky="ew", pady=5)

        self.classroom_var = tk.StringVar()
        ttk.Label(form, text="Salón").grid(row=5, column=0, sticky="w", pady=5)
        self.classroom_combo = ttk.Combobox(form, textvariable=self.classroom_var, state='readonly')
        self.classroom_combo.grid(row=5, column=1, sticky="ew", pady=5)

        self.schedule_var = tk.StringVar()
        ttk.Label(form, text="Horario").grid(row=6, column=0, sticky="w", pady=5)
        self.schedule_combo = ttk.Combobox(form, textvariable=self.schedule_var, state='readonly')
        self.schedule_combo.grid(row=6, column=1, sticky="ew", pady=5)

        self.semester_var = tk.StringVar()
        ttk.Label(form, text="Semestre").grid(row=7, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.semester_var).grid(row=7, column=1, sticky="ew", pady=5)

        self.max_students_var = tk.StringVar()
        ttk.Label(form, text="Máx. alumnos").grid(row=8, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.max_students_var).grid(row=8, column=1, sticky="ew", pady=5)

        buttons = ttk.Frame(form)
        buttons.grid(row=9, column=0, columnspan=2, pady=15)
        ttk.Button(buttons, text="Nuevo", command=self._reset).grid(row=0, column=0, padx=5)
        ttk.Button(buttons, text="Guardar", command=self._save).grid(row=0, column=1, padx=5)
        ttk.Button(buttons, text="Eliminar", command=self._delete).grid(row=0, column=2, padx=5)

        ttk.Label(form, text="Alumnos inscritos").grid(row=10, column=0, sticky="w", pady=(15, 5))
        students_columns = ('studentId', 'name', 'email', 'status')
        self.students_tree = ttk.Treeview(form, columns=students_columns, show='headings', height=6)
        headers_students = {
            'studentId': 'ID',
            'name': 'Nombre',
            'email': 'Correo',
            'status': 'Estado'
        }
        for col in students_columns:
            self.students_tree.heading(col, text=headers_students[col])
            self.students_tree.column(col, stretch=True)
        self.students_tree.grid(row=10, column=1, sticky="nsew")
        form.rowconfigure(10, weight=1)

    def _fetch_support_data(self) -> None:
        self.careers = self.api.get('/careers')
        self.career_combo.configure(values=[f"{item['id']} - {item['name']}" for item in self.careers])

        subjects = self.api.get('/subjects')
        for subject in subjects:
            self.subjects_by_career.setdefault(subject['careerId'], []).append(subject)
        self._refresh_subject_combo()

        self.teachers = self.api.get('/teachers')
        self.teacher_combo.configure(values=[f"{item['id']} - {item['name']}" for item in self.teachers])

        self.classrooms = self.api.get('/classrooms')
        self.classroom_combo.configure(values=[f"{item['id']} - {item['name']}" for item in self.classrooms])

        self.schedules = self.api.get('/schedules')
        self.schedule_combo.configure(values=[f"{item['id']} - {item['time']} ({item['shift']})" for item in self.schedules])

    def _refresh_subject_combo(self) -> None:
        if not self.career_var.get():
            self.subject_combo.configure(values=[])
            return
        career_id = int(self.career_var.get().split(' - ')[0])
        subjects = self.subjects_by_career.get(career_id, [])
        values = [f"{item['id']} - {item['name']}" for item in subjects]
        current = self.subject_var.get()
        self.subject_combo.configure(values=values)
        if current not in values and values:
            self.subject_var.set(values[0])

    def _load_groups(self) -> None:
        groups = self.api.get('/groups')
        self.tree.delete(*self.tree.get_children())
        for group in groups:
            self.tree.insert('', tk.END, values=(
                group['id'],
                group['name'],
                group.get('careerName', ''),
                group.get('subjectName', ''),
                group.get('teacherName', ''),
                f"{group.get('scheduleTime', '')}"
            ))

    def _on_select(self, _event: tk.Event) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        self._load_group(int(item['values'][0]))

    def _load_group(self, group_id: int) -> None:
        data = self.api.get(f'/groups/{group_id}')
        self.current_id = data['id']
        self.id_var.set(str(data['id']))
        self.name_var.set(data['name'])
        self.semester_var.set(str(data['semester']))
        self.max_students_var.set(str(data['maxStudents']))

        if data.get('careerId'):
            self.career_var.set(f"{data['careerId']} - {data.get('careerName', '')}")
        if data.get('subjectId'):
            self.subject_var.set(f"{data['subjectId']} - {data.get('subjectName', '')}")
        if data.get('teacherId'):
            teacher_label = f"{data['teacherId']} - {data.get('teacherName', '')}"
            self.teacher_var.set(teacher_label)
        if data.get('classroomId'):
            classroom_label = f"{data['classroomId']} - {data.get('classroomName', '')}"
            self.classroom_var.set(classroom_label)
        if data.get('scheduleId'):
            schedule_label = f"{data['scheduleId']} - {data.get('scheduleTime', '')} ({data.get('scheduleShift', '')})"
            self.schedule_var.set(schedule_label)

        self._refresh_subject_combo()
        self._load_students(data.get('students', []))

    def _load_students(self, students: List[Dict[str, Any]]) -> None:
        self.students_tree.delete(*self.students_tree.get_children())
        for student in students:
            self.students_tree.insert('', tk.END, values=(student['studentId'], student['name'], student.get('email', ''), student['status']))

    def _collect_payload(self) -> Dict[str, Any]:
        required_fields = [
            (self.name_var.get().strip(), 'Nombre de grupo'),
            (self.career_var.get().strip(), 'Carrera'),
            (self.subject_var.get().strip(), 'Materia'),
            (self.teacher_var.get().strip(), 'Maestro'),
            (self.classroom_var.get().strip(), 'Salón'),
            (self.schedule_var.get().strip(), 'Horario'),
            (self.semester_var.get().strip(), 'Semestre'),
            (self.max_students_var.get().strip(), 'Máx. alumnos')
        ]
        for value, label in required_fields:
            if not value:
                raise ValueError(f'{label} es requerido')

        try:
            semester = int(self.semester_var.get())
            max_students = int(self.max_students_var.get())
        except ValueError as error:
            raise ValueError('Semestre y números de alumnos deben ser numéricos') from error

        return {
            'name': self.name_var.get().strip(),
            'careerId': int(self.career_var.get().split(' - ')[0]),
            'subjectId': int(self.subject_var.get().split(' - ')[0]),
            'teacherId': int(self.teacher_var.get().split(' - ')[0]),
            'classroomId': int(self.classroom_var.get().split(' - ')[0]),
            'scheduleId': int(self.schedule_var.get().split(' - ')[0]),
            'semester': semester,
            'maxStudents': max_students
        }

    def _save(self) -> None:
        try:
            payload = self._collect_payload()
        except ValueError as error:
            messagebox.showwarning("Validación", str(error))
            return
        try:
            if self.current_id is None:
                group = self.api.post('/groups', payload)
            else:
                group = self.api.put(f"/groups/{self.current_id}", payload)
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Error", str(error))
            return
        messagebox.showinfo("Éxito", "Grupo guardado")
        self._load_group(group['id'])
        self._load_groups()

    def _delete(self) -> None:
        if self.current_id is None:
            messagebox.showinfo("Operación", "Selecciona un grupo")
            return
        if not messagebox.askyesno("Eliminar", "¿Deseas eliminar el grupo?"):
            return
        try:
            self.api.delete(f"/groups/{self.current_id}")
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Error", str(error))
            return
        messagebox.showinfo("Éxito", "Grupo eliminado")
        self._reset()
        self._load_groups()

    def _reset(self) -> None:
        self.current_id = None
        self.id_var.set('')
        self.name_var.set('')
        self.semester_var.set('')
        self.max_students_var.set('')
        self.career_var.set('')
        self.subject_var.set('')
        self.teacher_var.set('')
        self.classroom_var.set('')
        self.schedule_var.set('')
        self.students_tree.delete(*self.students_tree.get_children())
