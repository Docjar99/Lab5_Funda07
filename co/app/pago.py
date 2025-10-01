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
        monto INTEGER, -- en centavos/sus unidades menores
        metodo TEXT,
        resultado TEXT,
        referencia TEXT,
        creado_en TEXT
    )''')
    conn.commit()
    conn.close()

# --------- UTIL: Luhn para validar tarjetas (sólo para mock/validación local) ----------
def luhn_checksum(card_number: str) -> bool:
    card_number = re.sub(r"\D", "", card_number)
    if not card_number:
        return False
    def digits_of(n):
        return [int(d) for d in n]
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(str(d*2)))
    return checksum % 10 == 0

# --------- MOCK processor ----------
def procesar_pago_mock(card_number, exp_month, exp_year, cvc, amount_cents, paciente_nombre):
    # Validaciones simples
    if not luhn_checksum(card_number):
        return False, "Número de tarjeta inválido (Luhn)."
    if len(cvc) < 3 or not cvc.isdigit():
        return False, "CVC inválido."
    # Aceptar tarjeta de prueba 4242... como "exitosa"
    card_compact = re.sub(r"\D", "", card_number)
    if card_compact.startswith("4242424242424242"):
        referencia = "MOCK-SUCC-" + datetime.utcnow().strftime("%Y%m%d%H%M%S")
        resultado = "approved"
    else:
        # Simular decline para otras tarjetas en modo mock
        referencia = "MOCK-DECL-" + datetime.utcnow().strftime("%Y%m%d%H%M%S")
        resultado = "declined"

    # Guardar pago en BD
    conn = conectar_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO pagos (paciente_nombre, monto, metodo, resultado, referencia, creado_en)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (paciente_nombre, amount_cents, "MOCK_CARD", resultado, referencia, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

    return resultado == "approved", f"{resultado}:{referencia}"

# --------- GUI ----------
def run_gui():
    crear_tabla_pagos()
    root = tk.Tk()
    root.title("Pagos - Simulación")
    root.geometry("420x380")

    tk.Label(root, text="Nombre del cliente").pack(anchor="w", padx=10, pady=(10,0))
    ent_name = tk.Entry(root, width=40)
    ent_name.pack(padx=10)

    tk.Label(root, text="Monto (USD)").pack(anchor="w", padx=10, pady=(10,0))
    ent_amount = tk.Entry(root, width=20)
    ent_amount.pack(padx=10)

    tk.Label(root, text="Tarjeta (16 dígitos) / Prueba: 4242 4242 4242 4242").pack(anchor="w", padx=10, pady=(10,0))
    ent_card = tk.Entry(root, width=30)
    ent_card.pack(padx=10)

    tk.Label(root, text="Expiración (MM)").pack(anchor="w", padx=10, pady=(10,0))
    ent_mon = tk.Entry(root, width=6)
    ent_mon.pack(padx=10)

    tk.Label(root, text="Año expiración (YYYY)").pack(anchor="w", padx=10, pady=(10,0))
    ent_year = tk.Entry(root, width=8)
    ent_year.pack(padx=10)

    tk.Label(root, text="CVC").pack(anchor="w", padx=10, pady=(10,0))
    ent_cvc = tk.Entry(root, width=6, show="*")
    ent_cvc.pack(padx=10)

    def on_pagar():
        name = ent_name.get().strip()
        amount = ent_amount.get().strip()
        card = ent_card.get().strip()
        mon = ent_mon.get().strip()
        year = ent_year.get().strip()
        cvc = ent_cvc.get().strip()
        if not name or not amount or not card or not mon or not year or not cvc:
            messagebox.showerror("Error", "Complete todos los campos.")
            return
        try:
            amount_float = float(amount)
            if amount_float <= 0:
                raise ValueError()
            amount_cents = int(round(amount_float * 100))
        except Exception:
            messagebox.showerror("Error", "Monto inválido.")
            return

        ok, msg = procesar_pago_mock(card, mon, year, cvc, amount_cents, name)
        if ok:
            messagebox.showinfo("Pago aprobado", f"Pago aprobado (mock). Ref: {msg}")
        else:
            messagebox.showerror("Pago rechazado", f"Pago rechazado (mock). Detalle: {msg}")

    btn = tk.Button(root, text="Procesar pago (modo MOCK)", command=on_pagar)
    btn.pack(pady=12)

    # Información / guía sobre cómo integrar con Stripe (solo texto, no ejecuta)
    txt = tk.Text(root, height=6, wrap="word")
    txt.pack(padx=10, pady=(6,10), fill="both")
    txt.insert("1.0", (
        "Nota: Prueba"
    ))
    txt.config(state="disabled")

    root.mainloop()

if __name__ == "__main__":
    run_gui()
