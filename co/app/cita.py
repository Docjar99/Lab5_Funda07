# appointments.py
import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
from datetime import datetime
DB_PATH = "clinic.db"

DOCTORES = [
    ("D01", "Dr. Juan Pérez - Medicina General"),
    ("D02", "Dra. María López - Pediatría"),
    ("D03", "Dr. Carlos Ruiz - Cardiología"),
    ("D04", "Dra. Ana Gómez - Ginecología"),
]

def conectar_db():
    conn = sqlite3.connect(DB_PATH)
    return conn

def crear_tablas():
    conn = conectar_db()
    c = conn.cursor()
    # tabla de pacientes (si no existe) para integridad
    c.execute('''
    CREATE TABLE IF NOT EXISTS pacientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        identificacion TEXT NOT NULL,
        telefono TEXT NOT NULL,
        fecha_nacimiento TEXT NOT NULL,
        creado_en TEXT
    )''')
    # tabla de citas
    c.execute('''
    CREATE TABLE IF NOT EXISTS citas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER,
        paciente_nombre TEXT,
        doctor_id TEXT NOT NULL,
        doctor_nombre TEXT NOT NULL,
        fecha TEXT NOT NULL,   -- YYYY-MM-DD
        hora TEXT NOT NULL,    -- HH:MM (24h)
        creado_en TEXT NOT NULL,
        FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
    )''')
    conn.commit()
    conn.close()

def listar_citas():
    conn = conectar_db()
    c = conn.cursor()
    c.execute("SELECT id, paciente_nombre, doctor_nombre, fecha, hora FROM citas ORDER BY fecha, hora")
    filas = c.fetchall()
    conn.close()
    return filas

def citas_para_doctor_en_fecha_hora(doctor_id, fecha, hora):
    conn = conectar_db()
    c = conn.cursor()
    c.execute("SELECT id FROM citas WHERE doctor_id=? AND fecha=? AND hora=?", (doctor_id, fecha, hora))
    res = c.fetchall()
    conn.close()
    return len(res) > 0

def crear_cita(paciente_nombre, paciente_id, doctor_id, doctor_nombre, fecha, hora):
    # validaciones basicas
    if not paciente_nombre or not doctor_id or not fecha or not hora:
        return False, "Complete todos los campos."

    # validar fecha/hora formato
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
    except ValueError:
        return False, "Fecha debe tener formato YYYY-MM-DD."
    try:
        datetime.strptime(hora, "%H:%M")
    except ValueError:
        return False, "Hora debe tener formato HH:MM (24h)."

    # comprobar conflicto
    if citas_para_doctor_en_fecha_hora(doctor_id, fecha, hora):
        return False, f"El {doctor_nombre} ya tiene una cita a las {hora} del {fecha}."

    conn = conectar_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO citas (paciente_id, paciente_nombre, doctor_id, doctor_nombre, fecha, hora, creado_en)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (paciente_id if paciente_id else None, paciente_nombre.strip(), doctor_id, doctor_nombre, fecha, hora, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return True, "Cita creada con éxito."

def eliminar_cita(cita_id):
    conn = conectar_db()
    c = conn.cursor()
    c.execute("DELETE FROM citas WHERE id=?", (cita_id,))
    conn.commit()
    conn.close()

# GUI
def run_gui():
    crear_tablas()
    root = tk.Tk()
    root.title("Citas - Agenda")
    root.geometry("800x500")

    frm = tk.Frame(root)
    frm.pack(padx=10, pady=10, fill="x")

    tk.Label(frm, text="Paciente (nombre)").grid(row=0, column=0, sticky="w")
    ent_paciente = tk.Entry(frm, width=30)
    ent_paciente.grid(row=0, column=1, padx=6)

    tk.Label(frm, text="Paciente ID (opcional)").grid(row=1, column=0, sticky="w")
    ent_pid = tk.Entry(frm, width=15)
    ent_pid.grid(row=1, column=1, sticky="w", padx=6)

    tk.Label(frm, text="Doctor").grid(row=0, column=2, sticky="w")
    doctor_vals = [f"{d[0]} - {d[1]}" for d in DOCTORES]
    cmb_doctor = ttk.Combobox(frm, values=doctor_vals, state="readonly", width=40)
    cmb_doctor.grid(row=0, column=3, padx=6)
    cmb_doctor.set(doctor_vals[0])

    tk.Label(frm, text="Fecha (YYYY-MM-DD)").grid(row=1, column=2, sticky="w")
    ent_fecha = tk.Entry(frm, width=15)
    ent_fecha.grid(row=1, column=3, sticky="w", padx=6)

    tk.Label(frm, text="Hora (HH:MM)").grid(row=2, column=2, sticky="w")
    ent_hora = tk.Entry(frm, width=10)
    ent_hora.grid(row=2, column=3, sticky="w", padx=6)

    def on_agendar():
        paciente_nombre = ent_paciente.get()
        pid_text = ent_pid.get().strip()
        paciente_id = int(pid_text) if pid_text.isdigit() else None
        doc = cmb_doctor.get()
        doctor_id = doc.split(" - ")[0]
        doctor_nombre = doc.split(" - ")[1] if " - " in doc else doc
        fecha = ent_fecha.get().strip()
        hora = ent_hora.get().strip()
        ok, msg = crear_cita(paciente_nombre, paciente_id, doctor_id, doctor_nombre, fecha, hora)
        if ok:
            messagebox.showinfo("Éxito", msg)
            ent_paciente.delete(0, tk.END)
            ent_pid.delete(0, tk.END)
            ent_fecha.delete(0, tk.END)
            ent_hora.delete(0, tk.END)
            cargar_tree()
        else:
            messagebox.showerror("Error", msg)

    btn_ag = tk.Button(frm, text="Agendar cita", command=on_agendar)
    btn_ag.grid(row=3, column=0, columnspan=2, pady=8)

    # Listado de citas
    cols = ("id", "paciente", "doctor", "fecha", "hora")
    tree = ttk.Treeview(root, columns=cols, show="headings", height=12)
    for c in cols:
        tree.heading(c, text=c.capitalize())
        tree.column(c, anchor="w")
    tree.pack(padx=10, pady=10, fill="both", expand=True)

    def cargar_tree():
        for i in tree.get_children():
            tree.delete(i)
        filas = listar_citas()
        for f in filas:
            tree.insert("", tk.END, values=f)
    cargar_tree()

    def on_eliminar():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una cita para eliminar.")
            return
        item = tree.item(sel[0])
        cid = item["values"][0]
        if messagebox.askyesno("Confirmar", f"Eliminar cita ID {cid}?"):
            eliminar_cita(cid)
            cargar_tree()

    btn_elim = tk.Button(root, text="Eliminar cita seleccionada", command=on_eliminar)
    btn_elim.pack(pady=6)

    root.mainloop()

if __name__ == "__main__":
    run_gui()
