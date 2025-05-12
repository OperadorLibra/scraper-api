from fastapi import FastAPI
from fastapi.responses import JSONResponse
import requests
from bs4 import BeautifulSoup
import re
from collections import Counter

app = FastAPI()

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def formatar_nome_time(nome):
    substituicoes = {
        "São Paulo FC": "São Paulo",
        "SC Internacional": "Internacional",
        "Atlético-MG": "Atlético Mineiro",
        "Athletico-PR": "Athletico Paranaense",
        "Cuiabá EC": "Cuiabá"
    }
    return substituicoes.get(nome.strip(), nome.strip())

def extrair_placar(texto):
    padrao = re.compile(r'(\d{1,2})\s*x\s*(\d{1,2})')
    match = padrao.search(texto)
    if match:
        return f"{match.group(1)}x{match.group(2)}"
    return None

def buscar_ge_placares(url):
    try:
        html = requests.get(url, headers=HEADERS, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        resultados = []

        jogos = soup.find_all("div", class_="feed-post-body") or soup.find_all("div", class_="resultado-conteudo")
        for el in jogos:
            texto = el.get_text(separator=" ").strip()
            placar = extrair_placar(texto)
            if placar:
                partes = texto.split("x")
                if len(partes) != 2:
                    continue
                time1 = formatar_nome_time(re.sub(r'[^a-zA-ZÀ-ÿ ]', '', partes[0])).strip()
                time2 = formatar_nome_time(re.sub(r'[^a-zA-ZÀ-ÿ ]', '', partes[1])).strip()
                resultados.append({
                    "time1": time1,
                    "time2": time2,
                    "placar": placar
                })
        return resultados
    except:
        return []

def agrupar_por_jogo(lista):
    agrupado = {}
    for jogo in lista:
        chave = (jogo["time1"].lower(), jogo["time2"].lower())
        if chave not in agrupado:
            agrupado[chave] = []
        agrupado[chave].append(jogo["placar"])

    retorno = []
    for (time1, time2), placares in agrupado.items():
        consenso = Counter(placares).most_common(1)[0]
        retorno.append({
            "time1": time1.title(),
            "time2": time2.title(),
            "placares": placares,
            "placar_consenso": consenso[0] if consenso[1] > 1 else "divergente"
        })
    return retorno

@app.get("/rodada/{campeonato}")
def rodada(campeonato: str):
    urls = {
        "brasileirao": "https://ge.globo.com/futebol/brasileirao-serie-a/",
        "libertadores": "https://ge.globo.com/futebol/libertadores/",
        "sulamericana": "https://ge.globo.com/futebol/copa-sul-americana/",
        "copadobrasil": "https://ge.globo.com/futebol/copa-do-brasil/"
    }

    if campeonato not in urls:
        return JSONResponse(content={"erro": "Campeonato inválido"}, status_code=400)

    jogos = buscar_ge_placares(urls[campeonato])
    return agrupar_por_jogo(jogos)

@app.get("/")
def home():
    return {
        "status": "ok",
        "rotas": [
            "/rodada/brasileirao",
            "/rodada/libertadores",
            "/rodada/sulamericana",
            "/rodada/copadobrasil"
        ]
    }
