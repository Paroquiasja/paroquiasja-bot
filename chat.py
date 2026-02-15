def carregar_base():
    with open("base.txt", "r", encoding="utf-8") as f:
        linhas = [l.strip() for l in f.readlines() if l.strip()]

    base = []
    i = 0

    while i < len(linhas):
        if linhas[i].startswith("[") and linhas[i].endswith("]"):
            titulo = linhas[i]
            palavras = linhas[i + 1].split(",")
            resposta = linhas[i + 2]

            palavras = [p.strip().lower() for p in palavras]

            base.append({
                "titulo": titulo,
                "palavras": palavras,
                "resposta": resposta
            })

            i += 3
        else:
            i += 1

    return base


base = carregar_base()

print("Olá! Sou a IA da paróquia (versão de teste).")
print("Faça uma pergunta ou digite 'sair' para encerrar.")

while True:
    pergunta = input("Você: ").lower()

    if pergunta == "sair":
        print("IA: Até logo! Deus te abençoe 🙏")
        break

    melhor_item = None
    melhor_pontuacao = 0

    for item in base:
        pontos = 0
        for palavra in item["palavras"]:
            if palavra in pergunta:
                pontos += 1

        if pontos > melhor_pontuacao:
            melhor_pontuacao = pontos
            melhor_item = item

    if melhor_item and melhor_pontuacao > 0:
        print("IA:", melhor_item["resposta"])
    else:
        print("IA: Ainda não encontrei essa resposta na minha base. Tente perguntar de outro jeito.")