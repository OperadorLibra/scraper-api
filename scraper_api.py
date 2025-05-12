from fastapi import FastAPI
from fastapi.responses import JSONResponse
import requests
from bs4 import BeautifulSoup
from collections import Counter
import re

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
    padrao = re.compile(r'(\\d{1,2})\\s*x\\s*(\\d{1,2})')
    match = padrao.search(texto)
    if match:
        return f"{match.group(1)}x{match.group(2)}"
    return None

def buscar_resultados_site(url, tag_type="div", class_name=None):
    try:
        html = requests.get(url, headers=HEADERS, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        resultados = []
        elementos = soup.find_all(tag_type, class_=class_name) if class_name else soup.find_all(tag_type)

        for el in elementos:
            texto = el.get_text()
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

def agrupar_por_jogo(resultados_multiplos):
    agrupados = {}
    for fonte in resultados_multiplos:
        for jogo in fonte:
            chave = (jogo['time1'].lower(), jogo['time2'].lower())
            if chave not in agrupados:
                agrupados[chave] = []
            agrupados[chave].append(jogo['placar'])

    resposta = []
    for (time1, time2), placares in agrupados.items():
        consenso = Counter(placares).most_common(1)[0]
        resposta.append({
            "time1": time1.title(),
            "time2": time2.title(),
            "placares": placares,
            "placar_consenso": consenso[0] if consenso[1] > 1 else "divergente"
        })
    return resposta

@app.get("/rodada/{campeonato}")
def rodada(campeonato: str):
    if campeonato not in ["brasileirao", "libertadores", "sulamericana", "copadobrasil"]:
        return JSONResponse(content={"erro": "Campeonato inválido"}, status_code=400)

    fontes = [
        buscar_resultados_site("https://ge.globo.com/futebol/brasileirao-serie-a/", class_name="feed-post"),
        buscar_resultados_site("https://esporte.uol.com.br/futebol/"),
        buscar_resultados_site("https://www.espn.com.br/futebol/")
    ]

    agrupado = agrupar_por_jogo(fontes)
    return agrupado

@app.get("/")
def index():
    return {
        "status": "ok",
        "rotas": [
            "/rodada/brasileirao",
            "/rodada/libertadores",
            "/rodada/sulamericana",
            "/rodada/copadobrasil"
        ]
    }
