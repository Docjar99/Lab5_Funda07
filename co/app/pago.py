# payments.py
import tkinter as tk
from tkinter import messagebox
import sqlite3
from datetime import datetime
import re

DB_PATH = "clinic.db"

def conectar_db():
    return sqlite3.connect(DB_PATH)

def crear_tabla_pagos():
    conn = conectar_db()
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS pagos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_nombre TEXT,
        monto INTEGER,
        metodo TEXT,
        resultado TEXT,
        referencia TEXT,
        creado_en TEXT
    )''')
    conn.commit()
    conn.close()

# ---------------- UTILS -----------------
def luhn_checksum(card_number: str) -> bool:
    """Validación Luhn para tarjeta (mock)."""
    card_number = re.sub(r"\D", "", card_number)
    if not card_number:
        return False
    digits = [int(d) for d in card_number]
    odd = digits[-1::-2]
    even = digits[-2::-2]
    checksum = sum(odd)
    for d in even:
        checksum += sum([int(x) for x in str(d*2)])
    return checksum % 10 == 0

# ---------------- Procesadores Mock -----------------
def procesar_pago_credito(card_number, exp_month, exp_year, cvc, amount_cents, paciente_nombre):
    if not luhn_checksum(card_number):
        return False, "Tarjeta inválida (Luhn)."
    if len(cvc) < 3 or not cvc.isdigit():
        return False, "CVC inválido."
    card_digits = re.sub(r"\D", "", card_number)
    if card_digits == "4242424242424242":
        resultado, referencia = "approved", "CC-SUCC-" + datetime.utcnow().strftime("%Y%m%d%H%M%S")
    else:
        resultado, referencia = "declined", "CC-DECL-" + datetime.utcnow().strftime("%Y%m%d%H%M%S")

    guardar_pago(paciente_nombre, amount_cents, "CREDITO", resultado, referencia)
    return resultado == "approved", f"{resultado}:{referencia}"

def procesar_pago_paypal(email, amount_cents, paciente_nombre):
    if "@" not in email or "." not in email:
        return False, "Email PayPal inválido."
    resultado, referencia = "approved", "PP-" + datetime.utcnow().strftime("%Y%m%d%H%M%S")
    guardar_pago(paciente_nombre, amount_cents, "PAYPAL", resultado, referencia)
    return True, f"{resultado}:{referencia}"

def procesar_pago_transfer(ref, amount_cents, paciente_nombre):
    if len(ref) < 5:
        return False, "Referencia bancaria demasiado corta."
    resultado, referencia = "pending", f"TRANSF-{ref}"
    guardar_pago(paciente_nombre, amount_cents, "TRANSFERENCIA", resultado, referencia)
    return True, f"{resultado}:{referencia}"

def guardar_pago(nombre, monto, metodo, resultado, referencia):
    conn = conectar_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO pagos (paciente_nombre, monto, metodo, resultado, referencia, creado_en)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (nombre, monto, metodo, resultado, referencia, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

# ---------------- GUI -----------------
def run_gui():
    crear_tabla_pagos()
    root = tk.Tk()
    root.title("Pagos - Múltiples Métodos")
    root.geometry("500x500")

    tk.Label(root, text="Nombre del cliente").pack(anchor="w", padx=10, pady=(10,0))
    ent_name = tk.Entry(root, width=40)
    ent_name.pack(padx=10)

    tk.Label(root, text="Monto (USD)").pack(anchor="w", padx=10, pady=(10,0))
    ent_amount = tk.Entry(root, width=20)
    ent_amount.pack(padx=10)

    tk.Label(root, text="Método de pago").pack(anchor="w", padx=10, pady=(10,0))
    metodo_var = tk.StringVar(value="CREDITO")
    opciones = ["CREDITO", "PAYPAL", "TRANSFERENCIA"]
    frm_met = tk.Frame(root)
    frm_met.pack(padx=10, pady=5, anchor="w")
    for opt in opciones:
        tk.Radiobutton(frm_met, text=opt.title(), variable=metodo_var, value=opt, command=lambda: mostrar_formulario()).pack(side="left", padx=5)

    # ---- Formularios dinámicos ----
    frm_fields = tk.Frame(root)
    frm_fields.pack(padx=10, pady=10, fill="x")

    campos = {}

    def mostrar_formulario():
        for widget in frm_fields.winfo_children():
            widget.destroy()
        campos.clear()
        metodo = metodo_var.get()
        if metodo == "CREDITO":
            tk.Label(frm_fields, text="Tarjeta (16 dígitos)").grid(row=0, column=0, sticky="w")
            campos["card"] = tk.Entry(frm_fields, width=25)
            campos["card"].grid(row=0, column=1)

            tk.Label(frm_fields, text="Exp (MM)").grid(row=1, column=0, sticky="w")
            campos["mon"] = tk.Entry(frm_fields, width=5)
            campos["mon"].grid(row=1, column=1, sticky="w")

            tk.Label(frm_fields, text="Exp (YYYY)").grid(row=2, column=0, sticky="w")
            campos["year"] = tk.Entry(frm_fields, width=8)
            campos["year"].grid(row=2, column=1, sticky="w")

            tk.Label(frm_fields, text="CVC").grid(row=3, column=0, sticky="w")
            campos["cvc"] = tk.Entry(frm_fields, width=6, show="*")
            campos["cvc"].grid(row=3, column=1, sticky="w")

        elif metodo == "PAYPAL":
            tk.Label(frm_fields, text="Correo PayPal").grid(row=0, column=0, sticky="w")
            campos["email"] = tk.Entry(frm_fields, width=30)
            campos["email"].grid(row=0, column=1)

        elif metodo == "TRANSFERENCIA":
            tk.Label(frm_fields, text="Referencia bancaria").grid(row=0, column=0, sticky="w")
            campos["ref"] = tk.Entry(frm_fields, width=25)
            campos["ref"].grid(row=0, column=1)

    mostrar_formulario()

    def on_pagar():
        name = ent_name.get().strip()
        amount = ent_amount.get().strip()
        metodo = metodo_var.get()
        if not name or not amount:
            messagebox.showerror("Error", "Complete nombre y monto.")
            return
        try:
            amount_cents = int(round(float(amount) * 100))
            if amount_cents <= 0:
                raise ValueError()
        except:
            messagebox.showerror("Error", "Monto inválido.")
            return

        if metodo == "CREDITO":
            card = campos["card"].get().strip()
            mon = campos["mon"].get().strip()
            year = campos["year"].get().strip()
            cvc = campos["cvc"].get().strip()
            ok, msg = procesar_pago_credito(card, mon, year, cvc, amount_cents, name)
        elif metodo == "PAYPAL":
            email = campos["email"].get().strip()
            ok, msg = procesar_pago_paypal(email, amount_cents, name)
        elif metodo == "TRANSFERENCIA":
            ref = campos["ref"].get().strip()
            ok, msg = procesar_pago_transfer(ref, amount_cents, name)
        else:
            ok, msg = False, "Método no soportado."

        if ok:
            messagebox.showinfo("Pago registrado", f"Éxito ({metodo}). Ref: {msg}")
        else:
            messagebox.showerror("Error de pago", msg)

    btn = tk.Button(root, text="Procesar Pago", command=on_pagar)
    btn.pack(pady=15)

    root.mainloop()

if __name__ == "__main__":
    run_gui()
