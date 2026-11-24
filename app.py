from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session
)

import sqlite3
import os
import secrets
import hmac

from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent

DB_PATH = Path(
    os.environ.get("DB_PATH", str(BASE_DIR / "confirmacoes.db"))
)

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "chave-temporaria-local")


# --------------------------------------------------
# BANCO DE DADOS
# --------------------------------------------------

def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def iniciar_banco():

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

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


iniciar_banco()


# --------------------------------------------------
# PROTEÇÃO CONTRA CSRF
# --------------------------------------------------

def gerar_csrf():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)

    return session["csrf_token"]


app.jinja_env.globals["csrf_token"] = gerar_csrf


def validar_csrf():

    token = request.form.get("csrf_token", "")

    return hmac.compare_digest(
        session.get("csrf_token", ""),
        token
    )


# --------------------------------------------------
# PÁGINA PRINCIPAL
# --------------------------------------------------

@app.route("/")
def inicio():
    return render_template("index.html")


# --------------------------------------------------
# CONFIRMAR PRESENÇA
# --------------------------------------------------

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
        """, (
            nome,
            resposta,
            acompanhantes,
            telefone,
            observacao,
            datetime.now().isoformat(timespec="seconds")
        ))

    flash("✅ Sua confirmação para o evento foi enviada com sucesso! ❤️🖤", "sucesso")

    return redirect(url_for("inicio") + "#confirmar")


# --------------------------------------------------
# LOGIN DO RESUMO
# --------------------------------------------------

@app.route("/resumo/login", methods=["GET", "POST"])
def login_resumo():

    if session.get("resumo_autorizado"):
        return redirect(url_for("resumo"))

    if request.method == "POST":

        if not validar_csrf():
            flash("Solicitação inválida. Tente novamente.", "erro")
            return redirect(url_for("login_resumo"))

        senha_correta = os.environ.get("RESUMO_SENHA")

        if not senha_correta:
            flash("A senha ainda não foi configurada no servidor.", "erro")
            return redirect(url_for("login_resumo"))

        senha_digitada = request.form.get("senha", "")

        if hmac.compare_digest(senha_digitada, senha_correta):

            session.clear()
            session["resumo_autorizado"] = True
            gerar_csrf()

            return redirect(url_for("resumo"))

        flash("Senha incorreta. Tente novamente.", "erro")

    return render_template("resumo_login.html")


# --------------------------------------------------
# RESUMO DAS CONFIRMAÇÕES
# --------------------------------------------------

@app.route("/resumo")
def resumo():

    if not session.get("resumo_autorizado"):
        return redirect(url_for("login_resumo"))

    with conectar() as conn:

        total = conn.execute("""
            SELECT COUNT(*) AS n
            FROM confirmacoes
            WHERE resposta='sim'
        """).fetchone()["n"]

        pessoas = conn.execute("""
            SELECT COALESCE(SUM(1 + acompanhantes), 0) AS n
            FROM confirmacoes
            WHERE resposta='sim'
        """).fetchone()["n"]

        registros = conn.execute("""
            SELECT id, nome, resposta, acompanhantes,
                   telefone, observacao, criado_em
            FROM confirmacoes
            ORDER BY id DESC
        """).fetchall()

    return render_template(
        "resumo.html",
        total=total,
        pessoas=pessoas,
        registros=registros
    )


# --------------------------------------------------
# EXCLUIR CONFIRMAÇÃO
# --------------------------------------------------

@app.route("/resumo/excluir/<int:id>", methods=["POST"])
def excluir_confirmacao(id):

    if not session.get("resumo_autorizado"):
        return redirect(url_for("login_resumo"))

    if not validar_csrf():
        flash("Solicitação inválida.", "erro")
        return redirect(url_for("resumo"))

    with conectar() as conn:

        cursor = conn.execute(
            "DELETE FROM confirmacoes WHERE id = ?",
            (id,)
        )

        if cursor.rowcount:
            flash("Confirmação excluída com sucesso!", "sucesso")
        else:
            flash("Confirmação não encontrada.", "erro")

    return redirect(url_for("resumo"))


# --------------------------------------------------
# SAIR DO RESUMO
# --------------------------------------------------

@app.route("/resumo/sair", methods=["POST"])
def sair_resumo():

    if not validar_csrf():
        flash("Solicitação inválida.", "erro")
        return redirect(url_for("inicio"))

    session.clear()

    flash("Você saiu da área de confirmações.", "sucesso")

    return redirect(url_for("inicio"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)