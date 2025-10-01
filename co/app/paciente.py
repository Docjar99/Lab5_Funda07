# patients.py
import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
from datetime import datetime
import os

DB_PATH = "clinic.db"

def conectar_db():
    conn = sqlite3.connect(DB_PATH)
    return conn

def crear_tablas():
    conn = conectar_db()
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS pacientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        identificacion INTEGER NOT NULL,
        telefono TEXT NOT NULL,
        fecha_nacimiento TEXT NOT NULL,
        creado_en TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

def validar_identificacion(ident):
    return len(ident) == 8 and ident.isdigit()

def validar_telefono(tel):
    return len(tel) >= 10 and tel.isdigit()

def registrar_paciente(nombre, identificacion, telefono, fecha_nacimiento):
    if not nombre or not identificacion or not telefono or not fecha_nacimiento:
        return False, "Complete todos los campos."
    if not validar_identificacion(identificacion):
        return False, "La identificación debe tener exactamente 8 dígitos numéricos."
    if not validar_telefono(telefono):
        return False, "El teléfono debe tener al menos 10 dígitos numéricos."
    try:
        fecha = datetime.strptime(fecha_nacimiento, "%Y-%m-%d")
    except ValueError:
        return False, "La fecha debe tener formato YYYY-MM-DD."

    conn = conectar_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO pacientes (nombre, identificacion, telefono, fecha_nacimiento, creado_en)
        VALUES (?, ?, ?, ?, ?)
    ''', (nombre.strip(), identificacion.strip(), telefono.strip(), fecha.strftime("%Y-%m-%d"), datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return True, "Paciente registrado."

def listar_pacientes():
    conn = conectar_db()
    c = conn.cursor()
    c.execute("SELECT id, nombre, identificacion, telefono, fecha_nacimiento FROM pacientes ORDER BY nombre")
    filas = c.fetchall()
    conn.close()
    return filas

def buscar_pacientes(text):
    conn = conectar_db()
    c = conn.cursor()
    q = f"%{text}%"
    c.execute("SELECT id, nombre, identificacion, telefono, fecha_nacimiento FROM pacientes WHERE nombre LIKE ? OR identificacion LIKE ? ORDER BY nombre", (q,q))
    filas = c.fetchall()
    conn.close()
    return filas

def eliminar_paciente(paciente_id):
    conn = conectar_db()
    c = conn.cursor()
    c.execute("DELETE FROM pacientes WHERE id=?", (paciente_id,))
    conn.commit()
    conn.close()

# ---- GUI ----
def run_gui():
    crear_tablas()
    root = tk.Tk()
    root.title("Pacientes - Registro")
    root.geometry("700x450")

    frm_top = tk.Frame(root)
    frm_top.pack(padx=10, pady=10, fill="x")

    tk.Label(frm_top, text="Nombre").grid(row=0, column=0, sticky="w")
    entry_nombre = tk.Entry(frm_top, width=30)
    entry_nombre.grid(row=0, column=1, padx=6)

    tk.Label(frm_top, text="Identificación (8 dígitos)").grid(row=1, column=0, sticky="w")
    entry_ident = tk.Entry(frm_top, width=20)
    entry_ident.grid(row=1, column=1, sticky="w", padx=6)

    tk.Label(frm_top, text="Teléfono").grid(row=2, column=0, sticky="w")
    entry_tel = tk.Entry(frm_top, width=20)
    entry_tel.grid(row=2, column=1, sticky="w", padx=6)

    tk.Label(frm_top, text="Fecha nac. (YYYY-MM-DD)").grid(row=3, column=0, sticky="w")
    entry_fn = tk.Entry(frm_top, width=20)
    entry_fn.grid(row=3, column=1, sticky="w", padx=6)

    def on_registrar():
        nombre = entry_nombre.get()
        ident = entry_ident.get()
        tel = entry_tel.get()
        fn = entry_fn.get()
        ok, msg = registrar_paciente(nombre, ident, tel, fn)
        if ok:
            messagebox.showinfo("Éxito", msg)
            entry_nombre.delete(0, tk.END)
            entry_ident.delete(0, tk.END)
            entry_tel.delete(0, tk.END)
            entry_fn.delete(0, tk.END)
            cargar_tree()
        else:
            messagebox.showerror("Error", msg)

    btn_reg = tk.Button(frm_top, text="Registrar Paciente", command=on_registrar)
    btn_reg.grid(row=4, column=0, columnspan=2, pady=8)

    frm_mid = tk.Frame(root)
    frm_mid.pack(padx=10, pady=6, fill="x")

    tk.Label(frm_mid, text="Buscar (nombre o ID):").grid(row=0, column=0, sticky="w")
    entry_buscar = tk.Entry(frm_mid, width=30)
    entry_buscar.grid(row=0, column=1, sticky="w", padx=6)

    def on_buscar(_=None):
        cargar_tree(entry_buscar.get())

    btn_buscar = tk.Button(frm_mid, text="Buscar", command=on_buscar)
    btn_buscar.grid(row=0, column=2, padx=6)

    # Treeview para listar pacientes
    cols = ("id", "nombre", "identificacion", "telefono", "fecha_nacimiento")
    tree = ttk.Treeview(root, columns=cols, show="headings", height=10)
    for c in cols:
        tree.heading(c, text=c.capitalize())
        tree.column(c, anchor="w")
    tree.pack(padx=10, pady=10, fill="both", expand=True)

    def cargar_tree(filtro=""):
        for i in tree.get_children():
            tree.delete(i)
        if filtro:
            filas = buscar_pacientes(filtro)
        else:
            filas = listar_pacientes()
        for f in filas:
            tree.insert("", tk.END, values=f)

    def on_eliminar():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un paciente para eliminar.")
            return
        item = tree.item(sel[0])
        pid = item["values"][0]
        if messagebox.askyesno("Confirmar", f"Eliminar paciente ID {pid}?"):
            eliminar_paciente(pid)
            cargar_tree()

    btn_elim = tk.Button(root, text="Eliminar paciente seleccionado", command=on_eliminar)
    btn_elim.pack(pady=6)

    cargar_tree()
    root.mainloop()

if __name__ == "__main__":
    run_gui()
