from flask import Flask, request, render_template_string, session, redirect, url_for
import re
import os
import random
from datetime import date, datetime
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = "paroquia.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE,
            senha_hash TEXT,
            perfil TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT,
            pergunta TEXT,
            resposta TEXT
        )
    """)

    # cria usuários iniciais se a tabela estiver vazia
    cur = conn.execute("SELECT COUNT(*) as total FROM usuarios")
    total = cur.fetchone()["total"]

    if total == 0:
        senha_padrao = "1234"
        usuarios_iniciais = [
            ("admin", generate_password_hash(senha_padrao), "admin"),
            ("secretaria", generate_password_hash(senha_padrao), "secretaria"),
            ("pascom", generate_password_hash(senha_padrao), "pascom"),
            ("padre", generate_password_hash(senha_padrao), "padre"),
        ]
        for u in usuarios_iniciais:
            conn.execute(
                "INSERT INTO usuarios (usuario, senha_hash, perfil) VALUES (?, ?, ?)",
                u
            )
        conn.commit()

    conn.close()

init_db()

def get_usuario(usuario):
    conn = get_db()
    cur = conn.execute("SELECT * FROM usuarios WHERE usuario = ?", (usuario,))
    user = cur.fetchone()
    conn.close()
    return user

def verificar_senha(senha_digitada, senha_hash_banco):
    return check_password_hash(senha_hash_banco, senha_digitada)

def salvar_historico(pergunta, resposta):
    conn = get_db()
    conn.execute(
        "INSERT INTO historico (data_hora, pergunta, resposta) VALUES (?, ?, ?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), pergunta, resposta)
    )
    conn.commit()
    conn.close()



# ---------- Config ----------
STOPWORDS = {
    "o", "a", "os", "as", "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "para", "por", "que", "e", "ou", "um", "uma", "como", "é", "ser", "ter", "ao", "aos"
}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "paroquia-secret-key")

# ---------- Usuários ----------
USUARIOS = {
    "secretaria": {"senha": "1234", "perfil": "secretaria"},
    "pascom": {"senha": "1234", "perfil": "pascom"},
    "padre": {"senha": "1234", "perfil": "padre"},
}

# ---------- Versículos ----------
VERSICULOS = [
    "“Eu sou o caminho, a verdade e a vida.” (Jo 14,6)",
    "“O Senhor é meu pastor, nada me faltará.” (Sl 23,1)",
    "“Tudo posso naquele que me fortalece.” (Fl 4,13)",
    "“Alegrai-vos sempre no Senhor.” (Fl 4,4)",
    "“Vinde a mim, todos os que estais cansados.” (Mt 11,28)",
    "“O amor tudo suporta, tudo crê, tudo espera.” (1Cor 13,7)"
]

def versiculo_do_dia():
    hoje = date.today().toordinal()
    random.seed(hoje)
    return random.choice(VERSICULOS)

# ---------- Backup ----------
def backup_arquivo(caminho):
    os.makedirs("backups", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome = os.path.basename(caminho).replace(".txt", "")
    nome_backup = f"backups/{nome}_{timestamp}.txt"
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            conteudo = f.read()
        with open(nome_backup, "w", encoding="utf-8") as b:
            b.write(conteudo)

# ---------- Base ----------
SECOES = {
    "missas": "data/missas.txt",
    "catequese": "data/catequese.txt",
    "eventos": "data/eventos.txt",
    "contato": "data/contato.txt",
    "sacramentos": "data/sacramentos.txt",
    "doutrina": "data/doutrina.txt",
    "sobre_paroquia": "data/sobre_paroquia.txt",
    "pastorais": "data/pastorais.txt",
    "comunidades": "data/comunidades.txt",
    "apologetica": "data/apologetica.txt",
    "duvidas": "data/duvidas.txt",
    "cic": "data/cic.txt",
}

def carregar_base():
    base = []
    for _, caminho in SECOES.items():
        if not os.path.exists(caminho):
            continue

        with open(caminho, "r", encoding="utf-8") as f:
            linhas = [l.strip() for l in f.readlines() if l.strip()]

        i = 0
        while i < len(linhas):
            if linhas[i].startswith("[") and linhas[i].endswith("]"):
                if i + 2 < len(linhas):
                    palavras = [p.strip().lower() for p in linhas[i + 1].split(",")]
                    resposta = linhas[i + 2]
                    base.append({"palavras": palavras, "resposta": resposta})
                    i += 3
                else:
                    i += 1
            else:
                i += 1
    return base

base = carregar_base()

# ---------- Util ----------
def normalizar(texto):
    texto = texto.lower()
    texto = re.sub(r"[^\w\sáéíóúâêôãõç]", " ", texto)
    palavras = texto.split()
    palavras = [p for p in palavras if p not in STOPWORDS]
    return texto, palavras

def escolher_resposta(pergunta):
    pergunta_norm, tokens = normalizar(pergunta)

    melhor_item = None
    melhor_pontos = 0

    for item in base:
        pontos = 0
        for chave in item["palavras"]:
            chave = chave.lower()
            if len(chave.split()) > 1 and chave in pergunta_norm:
                pontos += 5
            else:
                if chave in tokens:
                    pontos += 1

        if pontos > melhor_pontos:
            melhor_pontos = pontos
            melhor_item = item

    if melhor_item and melhor_pontos > 0:
        return melhor_item["resposta"]
    else:
        return "Ainda não encontrei essa resposta na minha base. Tente perguntar de outro jeito ou fale com a secretaria paroquial."

# ---------- HTML ----------
HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Caminho de Anchieta</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="/static/favicon.ico" type="image/x-icon">
<style>
body { margin:0; font-family: Arial, sans-serif; background:#0b2a4a; }

/* Topo */
.topo {
    background:white; padding:15px 20px; display:flex; align-items:center; justify-content:space-between;
    border-bottom:4px solid #d4a017; box-shadow:0 2px 8px rgba(0,0,0,0.15);
}
.topo img { height:90px; }
.titulo-container { text-align:center; flex:1; }
.titulo { font-size:32px; font-weight:bold; color:#0b2a4a; }
.subtitulo { font-size:14px; color:#555; }

/* Layout */
.container { display:flex; min-height: calc(100vh - 140px); }

/* Menu */
.menu {
    width:220px; background:#123c6b; padding:15px; color:white;
}
.menu h3 { margin-top:0; border-bottom:1px solid #ffffff55; padding-bottom:5px; }
.menu button {
    width:100%; margin:6px 0; padding:10px; border:none; border-radius:6px;
    background:#d4a017; color:#0b2a4a; font-weight:bold; cursor:pointer;
}
.menu button:hover { background:#e6b737; }

/* Chat */
.chat-area { flex:1; padding:20px; }
.chat-box {
    background:white; border-radius:12px; padding:15px; height:60vh; overflow-y:auto;
    box-shadow:0 4px 10px rgba(0,0,0,0.2);
}

/* Versículo */
.versiculo {
    background:#d4a017; color:#0b2a4a; padding:10px; border-radius:8px; margin-bottom:10px;
    text-align:center; font-weight:bold;
}

/* Balões */
.msg { margin:10px 0; display:flex; }
.msg.user { justify-content:flex-end; }
.msg.ia { justify-content:flex-start; }
.balao { max-width:70%; padding:10px 14px; border-radius:15px; }
.user .balao { background:#0b2a4a; color:white; border-bottom-right-radius:0; }
.ia .balao { background:#e9ecef; color:#000; border-bottom-left-radius:0; }

/* Entrada */
.form-area { margin-top:10px; display:flex; gap:10px; }
.form-area input {
    flex:1; padding:12px; border-radius:8px; border:1px solid #ccc;
}
.form-area button {
    padding:12px 16px; border-radius:8px; border:none; background:#0b2a4a; color:white; font-weight:bold;
    cursor:pointer;
}
.form-area button:hover { background:#123c6b; }

@media (max-width:700px) {
    .menu { display:none; }
    .topo img { height:60px; }
    .titulo { font-size:24px; }
}
</style>
</head>
<body>

<div class="topo">
    <img src="/static/logo_paroquia.png">
    <div class="titulo-container">
        <div class="titulo">Caminho de Anchieta</div>
        <div class="subtitulo">Assistente da Paróquia São José de Anchieta</div>
    </div>
    <img src="/static/logo_pascom.png">
</div>

<div class="container">

    <div class="menu">
        <h3>Menu</h3>
        <form method="post"><input type="hidden" name="pergunta" value="Qual o horário da missa?"><button>Missas</button></form>
        <form method="post"><input type="hidden" name="pergunta" value="O que é o Batismo?"><button>Sacramentos</button></form>
        <form method="post"><input type="hidden" name="pergunta" value="Como entrar na catequese?"><button>Catequese</button></form>
        <form method="post"><input type="hidden" name="pergunta" value="Qual o contato da secretaria paroquial?"><button>Contato</button></form>
        <form method="post" action="/limpar"><button>Limpar conversa</button></form>
        <br>
        <a href="/login" style="color:white;">Área Administrativa</a>
    </div>

    <div class="chat-area">
        <div class="versiculo">Versículo do dia: {{ versiculo }}</div>

        <div class="chat-box">
            {% for autor, texto in historico %}
                <div class="msg {{ autor }}">
                    <div class="balao">{{ texto }}</div>
                </div>
            {% endfor %}
        </div>

        <form method="post" class="form-area">
            <input type="text" name="pergunta" placeholder="Digite sua pergunta...">
            <button type="submit">Enviar</button>
        </form>
    </div>

</div>

</body>
</html>
"""

MENSAGEM_INICIAL = (
    "Olá! 👋 Seja bem-vindo ao Caminho de Anchieta.\n\n"
    "Sou o assistente da Paróquia São José de Anchieta.\n"
    "Você pode usar o menu ao lado ou digitar sua pergunta."
)

# ---------- Rotas ----------
@app.route("/", methods=["GET", "POST"])
def index():
    if "historico" not in session:
        session["historico"] = [("ia", MENSAGEM_INICIAL)]

    if request.method == "POST":
        pergunta = request.form.get("pergunta", "").strip()
        if pergunta:
            historico = session["historico"]
            historico.append(("user", pergunta))
            resposta = escolher_resposta(pergunta)
            historico.append(("ia", resposta))
            session["historico"] = historico

            salvar_historico(pergunta, resposta)

    return render_template_string(HTML, historico=session["historico"], versiculo=versiculo_do_dia())

@app.route("/limpar", methods=["POST"])
def limpar():
    session["historico"] = [("ia", MENSAGEM_INICIAL)]
    return redirect(url_for("index"))

@app.route("/login", methods=["GET", "POST"])
def login():
    erro = ""

    if request.method == "POST":
        user = request.form.get("usuario")
        senha = request.form.get("senha")

        u = get_usuario(user)

        if u and verificar_senha(senha, u["senha_hash"]):
            session["logado"] = True
            session["usuario"] = u["usuario"]
            session["perfil"] = u["perfil"]
            session["historico"] = []
            return redirect(url_for("admin"))
        else:
            erro = "Usuário ou senha inválidos"

    return render_template_string(f"""
    <html>
    <head>
        <title>Login - Caminho de Anchieta</title>
        <style>
            body {{ font-family: Arial; background:#0b2a4a; color:#0b2a4a; }}
            .box {{ background:white; padding:20px; border-radius:10px; width:300px; margin:80px auto; text-align:center; }}
            input {{ width:90%; padding:10px; margin:8px 0; }}
            button {{ padding:10px 15px; font-weight:bold; }}
            .erro {{ color:red; }}
        </style>
    </head>
    <body>
        <div class="box">
            <h2>Login Administrativo</h2>
            <form method="post">
                <input type="text" name="usuario" placeholder="Usuário" required><br>
                <input type="password" name="senha" placeholder="Senha" required><br>
                <button type="submit">Entrar</button>
            </form>
            <p class="erro">{erro}</p>
            <a href="/">Voltar ao chat</a>
        </div>
    </body>
    </html>
    """)

@app.route("/admin")
def admin():
    if not session.get("logado"):
        return redirect(url_for("login"))

    usuario = session.get("usuario", "")
    perfil = session.get("perfil", "")

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Painel Administrativo - Caminho de Anchieta</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body { margin:0; font-family: Arial, sans-serif; background:#0b2a4a; }

.topo {
    background:white; padding:15px 20px; display:flex; align-items:center; justify-content:space-between;
    border-bottom:4px solid #d4a017; box-shadow:0 2px 8px rgba(0,0,0,0.15);
}
.topo img { height:70px; }
.titulo { font-size:26px; font-weight:bold; color:#0b2a4a; }

.container { padding:30px; }

.info {
    color:white;
    margin-bottom:20px;
}

.grid {
    display:grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap:20px;
}

.card {
    background:white;
    border-radius:12px;
    padding:20px;
    text-align:center;
    box-shadow:0 4px 10px rgba(0,0,0,0.2);
    transition: transform 0.2s;
}

.card:hover { transform: translateY(-5px); }

.card h3 { margin-top:0; color:#0b2a4a; }
.card p { color:#555; }

.card a {
    display:inline-block;
    margin-top:10px;
    padding:10px 15px;
    background:#d4a017;
    color:#0b2a4a;
    text-decoration:none;
    border-radius:8px;
    font-weight:bold;
}

.card a:hover { background:#e6b737; }
</style>
</head>
<body>

<div class="topo">
    <img src="/static/logo_paroquia.png">
    <div class="titulo">Painel Administrativo - Caminho de Anchieta</div>
    <img src="/static/logo_pascom.png">
</div>

<div class="container">

    <div class="info">
        Usuário: <b>{{ usuario }}</b> | Perfil: <b>{{ perfil }}</b>
    </div>

    <div class="grid">

        <div class="card">
            <h3>✏️ Editor da Base</h3>
            <p>Editar a base de conhecimento do assistente.</p>
            <a href="/admin/editor">Acessar</a>
        </div>

        <div class="card">
            <h3>📜 Histórico</h3>
            <p>Em breve: ver perguntas e respostas.</p>
            <a href="/admin/historico">Acessar</a>
        </div>

        <div class="card">
            <h3>👥 Usuários</h3>
            <p>Em breve: gerenciar usuários.</p>
            <a href="/admin/usuarios">Acessar</a>
        </div>

        <div class="card">
            <h3>💬 Voltar ao Chat</h3>
            <p>Retornar ao assistente da paróquia.</p>
            <a href="/">Voltar</a>
        </div>

        <div class="card">
            <h3>🚪 Logout</h3>
            <p>Encerrar sua sessão com segurança.</p>
            <a href="/logout">Sair</a>
        </div>

    </div>
</div>

</body>
</html>
""", usuario=usuario, perfil=perfil)

@app.route("/admin/editor")
def admin_editor_home():
    if not session.get("logado"):
        return redirect(url_for("login"))

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Editor da Base - Caminho de Anchieta</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body { margin:0; font-family: Arial, sans-serif; background:#0b2a4a; }
.topo {
    background:white; padding:15px 20px; display:flex; align-items:center; justify-content:space-between;
    border-bottom:4px solid #d4a017; box-shadow:0 2px 8px rgba(0,0,0,0.15);
}
.topo img { height:70px; }
.titulo { font-size:26px; font-weight:bold; color:#0b2a4a; }

.container { padding:30px; }

.grid {
    display:grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap:20px;
}

.card {
    background:white;
    border-radius:12px;
    padding:20px;
    text-align:center;
    box-shadow:0 4px 10px rgba(0,0,0,0.2);
}

.card h3 { margin-top:0; color:#0b2a4a; }

.card a {
    display:inline-block;
    margin-top:10px;
    padding:10px 15px;
    background:#d4a017;
    color:#0b2a4a;
    text-decoration:none;
    border-radius:8px;
    font-weight:bold;
}
.card a:hover { background:#e6b737; }

.voltar {
    display:inline-block;
    margin-top:20px;
    color:white;
    text-decoration:none;
    font-weight:bold;
}
</style>
</head>
<body>

<div class="topo">
    <img src="/static/logo_paroquia.png">
    <div class="titulo">Escolha o que deseja editar</div>
    <img src="/static/logo_pascom.png">
</div>

<div class="container">
    <div class="grid">
        {% for k in secoes.keys() %}
        <div class="card">
            <h3>{{ k.replace("_"," ").title() }}</h3>
            <a href="/admin/editor/editar?secao={{ k }}">Editar</a>
        </div>
        {% endfor %}
    </div>

    <a class="voltar" href="/admin">⬅ Voltar ao painel</a>
</div>

</body>
</html>
""", secoes=SECOES)

@app.route("/admin/editor/editar", methods=["GET", "POST"])
def admin_editor_secao():
    if not session.get("logado"):
        return redirect(url_for("login"))

    secao = request.args.get("secao", "missas")
    if secao not in SECOES:
        return "Seção inválida", 404

    caminho = SECOES[secao]
    os.makedirs(os.path.dirname(caminho), exist_ok=True)

    mensagem = ""

    if request.method == "POST":
        novo_conteudo = request.form.get("base", "")
        backup_arquivo(caminho)
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(novo_conteudo)

        global base
        base = carregar_base()
        mensagem = "Seção atualizada com sucesso! (Backup criado automaticamente)"

    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            conteudo = f.read()
    else:
        conteudo = ""

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Editando {{ secao }}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body { margin:0; font-family: Arial, sans-serif; background:#0b2a4a; }
.topo {
    background:white; padding:15px 20px; border-bottom:4px solid #d4a017;
}
.container { padding:20px; }
.box {
    background:white; padding:20px; border-radius:12px; max-width:1100px; margin:auto;
}
textarea {
    width:100%; height:420px; padding:10px; font-family: monospace;
}
button {
    padding:10px 16px; border-radius:8px; border:none; background:#d4a017;
    font-weight:bold; color:#0b2a4a; cursor:pointer;
}
.msg { color:green; font-weight:bold; }
a { display:inline-block; margin-top:15px; font-weight:bold; color:#0b2a4a; text-decoration:none; }
</style>
</head>
<body>

<div class="topo">
    <b>Editando:</b> {{ secaootni.replace("_"," ").title() if False else secao.replace("_"," ").title() }}
</div>

<div class="container">
    <div class="box">
        {% if mensagem %}<div class="msg">{{ mensagem }}</div>{% endif %}

        <form method="post">
            <textarea name="base">{{ conteudo }}</textarea><br><br>
            <button type="submit">💾 Salvar</button>
        </form>

        <a href="/admin/editor">⬅ Voltar aos tópicos</a>
    </div>
</div>

</body>
</html>
""", secao=secao, conteudo=conteudo, mensagem=mensagem)

@app.route("/admin/historico")
def admin_historico():
    if not session.get("logado"):
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.execute("SELECT * FROM historico ORDER BY id DESC LIMIT 200")
    registros = cur.fetchall()
    conn.close()

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Histórico - Caminho de Anchieta</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body { margin:0; font-family: Arial, sans-serif; background:#0b2a4a; }
.topo {
    background:white; padding:15px 20px; border-bottom:4px solid #d4a017;
    font-size:24px; font-weight:bold; color:#0b2a4a;
}
.container { padding:20px; }
.box {
    background:white; padding:20px; border-radius:12px; max-width:1200px; margin:auto;
}
.item {
    border-bottom:1px solid #ddd;
    padding:10px 0;
}
.data { font-size:12px; color:#666; }
.pergunta { font-weight:bold; color:#0b2a4a; }
.resposta { margin-top:5px; }
a { display:inline-block; margin-top:15px; font-weight:bold; color:#0b2a4a; text-decoration:none; }
</style>
</head>
<body>

<div class="topo">📜 Histórico de Perguntas e Respostas</div>

<div class="container">
    <div class="box">
        {% for r in registros %}
            <div class="item">
                <div class="data">{{ r["data_hora"] }}</div>
                <div class="pergunta">❓ {{ r["pergunta"] }}</div>
                <div class="resposta">💬 {{ r["resposta"] }}</div>
            </div>
        {% endfor %}

        <a href="/admin">⬅ Voltar ao painel</a>
    </div>
</div>

</body>
</html>
""", registros=registros)

@app.route("/admin/usuarios", methods=["GET", "POST"])
def admin_usuarios():
    if not session.get("logado"):
        return redirect(url_for("login"))

    perfil_atual = session.get("perfil")
    if perfil_atual != "admin":
        return "Acesso restrito ao administrador", 403

    mensagem = ""

    if request.method == "POST":
        novo_usuario = request.form.get("usuario", "").strip()
        nova_senha = request.form.get("senha", "").strip()
        novo_perfil = request.form.get("perfil", "").strip()

        if not novo_usuario or not nova_senha or not novo_perfil:
            mensagem = "Preencha todos os campos."
        else:
            try:
                conn = get_db()
                conn.execute(
                    "INSERT INTO usuarios (usuario, senha_hash, perfil) VALUES (?, ?, ?)",
                    (novo_usuario, generate_password_hash(nova_senha), novo_perfil)
                )
                conn.commit()
                conn.close()
                mensagem = "Usuário criado com sucesso!"
            except sqlite3.IntegrityError:
                mensagem = "Esse usuário já existe."

    conn = get_db()
    cur = conn.execute("SELECT id, usuario, perfil FROM usuarios ORDER BY usuario")
    usuarios = cur.fetchall()
    conn.close()

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Gerenciar Usuários</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body { margin:0; font-family: Arial, sans-serif; background:#0b2a4a; }
.topo { background:white; padding:15px 20px; border-bottom:4px solid #d4a017; font-size:24px; font-weight:bold; color:#0b2a4a; }
.container { padding:20px; }
.box { background:white; padding:20px; border-radius:12px; max-width:1000px; margin:auto; }

table { width:100%; border-collapse:collapse; margin-top:20px; }
th, td { padding:8px; border-bottom:1px solid #ddd; text-align:left; }

input, select { padding:8px; margin:5px 0; width:100%; }
button { padding:10px 16px; border-radius:8px; border:none; background:#d4a017; font-weight:bold; color:#0b2a4a; cursor:pointer; }
.msg { margin-top:10px; font-weight:bold; color:green; }
.erro { margin-top:10px; font-weight:bold; color:red; }

a { display:inline-block; margin-top:15px; font-weight:bold; color:#0b2a4a; text-decoration:none; }
</style>
</head>
<body>

<div class="topo">👥 Gerenciar Usuários</div>

<div class="container">
<div class="box">

<h3>Criar novo usuário</h3>
<form method="post">
    <input type="text" name="usuario" placeholder="Usuário">
    <input type="password" name="senha" placeholder="Senha">
    <select name="perfil">
        <option value="">Selecione o perfil</option>
        <option value="admin">Admin</option>
        <option value="secretaria">Secretaria</option>
        <option value="pascom">Pascom</option>
        <option value="padre">Padre</option>
    </select>
    <button type="submit">➕ Criar usuário</button>
</form>

{% if mensagem %}
<div class="msg">{{ mensagem }}</div>
{% endif %}

<h3>Usuários cadastrados</h3>
<table>
<tr>
    <th>Usuário</th>
    <th>Perfil</th>
    <th>Ações</th>
</tr>
{% for u in usuarios %}
<tr>
    <td>{{ u["usuario"] }}</td>
    <td>{{ u["perfil"] }}</td>
    <td>
        {% if u["usuario"] != "admin" %}
            <a href="/admin/usuarios/excluir/{{ u['id'] }}">🗑 Excluir</a>
        {% else %}
            —
        {% endif %}
    </td>
</tr>
{% endfor %}
</table>

<a href="/admin">⬅ Voltar ao painel</a>

</div>
</div>

</body>
</html>
""", usuarios=usuarios, mensagem=mensagem)

@app.route("/admin/usuarios/excluir/<int:user_id>")
def excluir_usuario(user_id):
    if not session.get("logado"):
        return redirect(url_for("login"))

    if session.get("perfil") != "admin":
        return "Acesso restrito ao administrador", 403

    conn = get_db()
    conn.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("admin_usuarios"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# ---------- Run ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)




