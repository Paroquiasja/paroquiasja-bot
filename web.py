from flask import Flask, request, render_template_string
import re

# ---------- Config ----------
STOPWORDS = {
    "o", "a", "os", "as", "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "para", "por", "que", "e", "ou", "um", "uma", "como", "é", "ser", "ter", "ao", "aos"
}

# ---------- Base ----------
def carregar_base():
    with open("base.txt", "r", encoding="utf-8") as f:
        linhas = [l.strip() for l in f.readlines() if l.strip()]

    base = []
    i = 0
    while i < len(linhas):
        if linhas[i].startswith("[") and linhas[i].endswith("]"):
            palavras = [p.strip().lower() for p in linhas[i + 1].split(",")]
            resposta = linhas[i + 2]
            base.append({"palavras": palavras, "resposta": resposta})
            i += 3
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

            # Frase completa
            if len(chave.split()) > 1 and chave in pergunta_norm:
                pontos += 5
            else:
                # Palavra solta
                if chave in tokens:
                    pontos += 1

        if pontos > melhor_pontos:
            melhor_pontos = pontos
            melhor_item = item

    if melhor_item and melhor_pontos > 0:
        return melhor_item["resposta"]
    else:
        return "Ainda não encontrei essa resposta na minha base. Tente perguntar de outro jeito ou fale com a secretaria paroquial."

# ---------- Web ----------
app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Assistente da Paróquia</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f2f2f2; }
        .chat { max-width: 600px; margin: 40px auto; background: white; padding: 20px; border-radius: 8px; }
        .msg { margin: 10px 0; }
        .user { font-weight: bold; }
        .ia { color: #0b5ed7; }
        input[type=text] { width: 80%; padding: 8px; }
        button { padding: 8px 12px; }
    </style>
</head>
<body>
    <div class="chat">
        <h2>Assistente da Paróquia</h2>
        {% for autor, texto in historico %}
            <div class="msg"><span class="{{ autor }}">{{ autor }}:</span> {{ texto }}</div>
        {% endfor %}
        <form method="post">
            <input type="text" name="pergunta" placeholder="Digite sua pergunta..." autofocus>
            <button type="submit">Enviar</button>
        </form>
    </div>
</body>
</html>
"""

historico = [("ia", "Olá! Faça sua pergunta abaixo.")]

@app.route("/", methods=["GET", "POST"])
def index():
    global historico
    if request.method == "POST":
        pergunta = request.form.get("pergunta", "").strip()
        if pergunta:
            historico.append(("user", pergunta))
            resposta = escolher_resposta(pergunta)
            historico.append(("ia", resposta))
    return render_template_string(HTML, historico=historico)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
