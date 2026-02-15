import tkinter as tk
from tkinter import scrolledtext
import re

# ---------- Config ----------
STOPWORDS = {
    "o", "a", "os", "as", "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "para", "por", "que", "e", "ou", "um", "uma", "como", "é", "ser", "ter", "ao", "aos"
}

# ---------- Base de conhecimento ----------
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

# ---------- Lógica ----------
def responder(event=None):
    pergunta = entrada.get().strip()
    if not pergunta:
        return

    pergunta_norm, tokens = normalizar(pergunta)

    chat.config(state=tk.NORMAL)
    chat.insert(tk.END, f"Você: {pergunta}\n")

    melhor_item = None
    melhor_pontos = 0

    for item in base:
        pontos = 0
        for chave in item["palavras"]:
            chave = chave.lower()

            # Frase completa bate exatamente
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
        resposta = melhor_item["resposta"]
    else:
        resposta = "Ainda não encontrei essa resposta na minha base. Tente perguntar de outro jeito ou fale com a secretaria paroquial."

    chat.insert(tk.END, f"IA: {resposta}\n\n")
    chat.config(state=tk.DISABLED)
    chat.see(tk.END)

    entrada.delete(0, tk.END)
    entrada.focus_set()

# ---------- Interface ----------
janela = tk.Tk()
janela.title("Assistente da Paróquia")
janela.geometry("600x400")

chat = scrolledtext.ScrolledText(janela, wrap=tk.WORD, height=15)
chat.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
chat.insert(tk.END, "IA: Olá! Faça sua pergunta abaixo.\n\n")
chat.config(state=tk.DISABLED)

frame = tk.Frame(janela)
frame.pack(padx=10, pady=10, fill=tk.X)

entrada = tk.Entry(frame)
entrada.pack(side=tk.LEFT, fill=tk.X, expand=True)

botao = tk.Button(frame, text="Enviar", command=responder)
botao.pack(side=tk.RIGHT, padx=5)

entrada.focus_set()
janela.bind("<Return>", responder)

janela.mainloop()

