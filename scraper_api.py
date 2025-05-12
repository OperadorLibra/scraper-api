from fastapi import FastAPI
from fastapi.responses import JSONResponse
import requests
from bs4 import BeautifulSoup
from collections import Counter

app = FastAPI()

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def buscar_resultados_google(query):
    try:
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        html = requests.get(url, headers=HEADERS, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        resultados = []
        jogo_tags = soup.find_all('div', string=lambda s: s and 'x' in s and any(char.isdigit() for char in s))

        for tag in jogo_tags:
            texto = tag.get_text(strip=True)
            if texto.count('x') != 1:
                continue
            partes = texto.split('x')
            time1 = partes[0].strip()
            time2 = partes[1].strip()
            placar1 = ''.join(filter(str.isdigit, time1))
            placar2 = ''.join(filter(str.isdigit, time2))
            time1_nome = ''.join(filter(lambda c: not c.isdigit(), time1)).strip()
            time2_nome = ''.join(filter(lambda c: not c.isdigit(), time2)).strip()

            resultados.append({
                "time1": time1_nome,
                "time2": time2_nome,
                "placar": f"{placar1}x{placar2}"
            })
        return resultados
    except Exception:
        return []

def buscar_resultados_site(url, tag_type="div", class_name=None):
    try:
        html = requests.get(url, headers=HEADERS, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        resultados = []
        elementos = soup.find_all(tag_type, class_=class_name) if class_name else soup.find_all(tag_type)

        for el in elementos:
            texto = el.get_text()
            if "x" in texto and any(char.isdigit() for char in texto):
                partes = texto.split("x")
                time1 = partes[0].strip()
                time2 = partes[1].strip()
                placar1 = ''.join(filter(str.isdigit, time1))
                placar2 = ''.join(filter(str.isdigit, time2))
                time1_nome = ''.join(filter(lambda c: not c.isdigit(), time1)).strip()
                time2_nome = ''.join(filter(lambda c: not c.isdigit(), time2)).strip()
                resultados.append({
                    "time1": time1_nome,
                    "time2": time2_nome,
                    "placar": f"{placar1}x{placar2}"
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

    query = f"rodada {campeonato}"
    fontes = [
        buscar_resultados_google(query),
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
