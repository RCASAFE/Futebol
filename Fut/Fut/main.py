from dotenv import load_dotenv

load_dotenv()
import os
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session  #As sessions permitem guardar informações durante a naveção pelo site
)

from banco_dados.bd_exec import (
    criar_tabelas,
    cadastro_usuario,
    logando,
    adicionar_dados,
    tabela,
    deletar
)

app = Flask(__name__)

# Chaves configuradas no ambiente
app.secret_key = os.environ.get("FLASK_SECRET_KEY")


# Senha exclusiva do administrador
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

if not app.secret_key:
    raise RuntimeError("Configure a variável FLASK_SECRET_KEY.")

criar_tabelas()


# LOGIN - GET
@app.route("/", methods=["GET"])
def login():
    return render_template("index.html")


# LOGIN - POST
@app.route("/", methods=["POST"])
def logar():
    nome = request.form.get("nome", "").strip()#Strip é para remover espaços atraz e na parte da frente da string, mas não remove entre palavras
    senha = request.form.get("senha", "")

    # Verifica se é o administrador
    if nome.lower() == "adm":
        if ADMIN_PASSWORD and senha == ADMIN_PASSWORD:
            session.clear()
            session["adm"] = True #Está session guarda que o usuario é um adm
            print("Nome recebido:", repr(nome))
            return redirect(url_for("painel_admin"))
        

        return render_template(
            "index.html",
            erro="Nome ou senha incorretos."
        )

    # Verifica se é um usuário comum
    id_usuario = logando(nome, senha)

    if id_usuario is not None:
        session.clear()
        session["usuario_id"] = id_usuario #Está session guarda que o usuario é commun(não adm)
        session["adm"] = False

        return redirect(url_for("mostrar"))

    return render_template(
        "index.html",
        erro="Nome ou senha incorretos."
    )


# CADASTRO - GET
@app.route("/cadastro", methods=["GET"])
def cadastro():
    return render_template("cadastro.html")


# CADASTRO - POST
@app.route("/cadastro", methods=["POST"])
def cadastrar():
    nome = request.form.get("nome", "").strip()
    senha = request.form.get("senha", "")

    # Impede que alguém cadastre o nome reservado do administrador
    if nome.lower() == "adm":
        return render_template(
            "cadastro.html",
            erro="Esse nome não está disponível."
        )

    id_usuario = cadastro_usuario(nome, senha)

    if id_usuario is not None:
        session.clear()
        session["usuario_id"] = id_usuario
        session["admin"] = False

        return redirect(url_for("mostrar"))

    return render_template(
        "cadastro.html",
        erro="Não foi possível realizar o cadastro. Verifique se o nome já existe."
    )
    


# RANKING - SOMENTE USUÁRIOS LOGADOS
@app.route("/placar", methods=["GET"])
def mostrar():
    if "usuario_id" not in session and not session.get("admin"):
        return redirect(url_for("login"))

    placares = tabela()

    return render_template(
        "placar.html",
        placares=placares
    )


# PAINEL DO ADMINISTRADOR
@app.route("/painel-admin", methods=["GET"])
def painel_admin():
    if not session.get("adm"):
        return redirect(url_for("login"))

    return render_template("adm.html")


# ATUALIZAR ESTATÍSTICAS - SOMENTE ADMIN
@app.route("/atualizar-placar", methods=["POST"])
def atualizar_placar():
    if not session.get("adm"):
        return redirect(url_for("login"))

    try:
        id_usuario = int(request.form.get("id_usuario", ""))
        gols = int(request.form.get("gols", ""))
        assistencias = int(request.form.get("assistencias", ""))
        jogos = int(request.form.get("jogos", "1"))
        escolha = request.form.get("escolha", "")

       

        if min(id_usuario, gols, assistencias) < 0 or id_usuario == 0:
            raise ValueError

        if jogos < 1:
            raise ValueError

        sucesso = adicionar_dados(
            id_usuario,
            gols,
            assistencias,
            jogos
        )

        if sucesso:
            return render_template(
                "adm.html",
                mensagem="Estatísticas atualizadas!"
            )

        return render_template(
            "adm.html",
            mensagem="Não foi possível atualizar as estatísticas."
        )

    except (ValueError, TypeError):
        return render_template(
            "adm.html",
            mensagem="Verifique os valores informados."
        )


# LOGOUT
@app.route("/sair", methods=["GET"])
def sair():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
