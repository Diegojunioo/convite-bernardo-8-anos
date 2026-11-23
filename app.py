from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "confirmacoes.db"

app = Flask(__name__)
app.secret_key = "troque-esta-chave-antes-de-publicar"

def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def iniciar_banco():
    with conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS confirmacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                resposta TEXT NOT NULL,
                acompanhantes INTEGER NOT NULL DEFAULT 0,
                telefone TEXT,
                observacao TEXT,
                criado_em TEXT NOT NULL
            )
        """)

@app.route("/")
def inicio():
    return render_template("index.html")

@app.route("/confirmar", methods=["POST"])
def confirmar():
    nome = request.form.get("nome", "").strip()
    resposta = request.form.get("resposta", "").strip()
    telefone = request.form.get("telefone", "").strip()
    observacao = request.form.get("observacao", "").strip()

    try:
        acompanhantes = int(request.form.get("acompanhantes", "0"))
    except ValueError:
        acompanhantes = 0

    if not nome or resposta not in ("sim", "nao"):
        flash("Informe seu nome e selecione uma resposta.", "erro")
        return redirect(url_for("inicio") + "#confirmar")

    acompanhantes = max(0, min(acompanhantes, 10))
    if resposta == "nao":
        acompanhantes = 0

    with conectar() as conn:
        conn.execute("""
            INSERT INTO confirmacoes
            (nome, resposta, acompanhantes, telefone, observacao, criado_em)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nome, resposta, acompanhantes, telefone, observacao,
              datetime.now().isoformat(timespec="seconds")))

    flash("Resposta recebida! Obrigado por confirmar. ❤️🖤", "sucesso")
    return redirect(url_for("inicio") + "#confirmar")

@app.route("/resumo")
def resumo():
    # Página simples para a família consultar as confirmações.
    # Antes de publicar, proteja esta rota com autenticação ou remova-a.
    with conectar() as conn:
        total = conn.execute("""
            SELECT COUNT(*) AS n FROM confirmacoes WHERE resposta='sim'
        """).fetchone()["n"]
        pessoas = conn.execute("""
            SELECT COALESCE(SUM(1 + acompanhantes), 0) AS n
            FROM confirmacoes WHERE resposta='sim'
        """).fetchone()["n"]
        registros = conn.execute("""
            SELECT nome, resposta, acompanhantes, telefone, observacao, criado_em
            FROM confirmacoes ORDER BY id DESC
        """).fetchall()
    return render_template("resumo.html", total=total, pessoas=pessoas, registros=registros)

if __name__ == "__main__":
    iniciar_banco()
    app.run(host="0.0.0.0", port=5000, debug=True)
