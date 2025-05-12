from fastapi import FastAPI
from fastapi.responses import JSONResponse
import requests
from bs4 import BeautifulSoup

app = FastAPI()

def buscar_resultados_por_campeonato(campeonato_nome):
    query = f"rodada {campeonato_nome}"
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    headers = { "User-Agent": "Mozilla/5.0" }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return {"erro": "Erro ao acessar Google"}

    soup = BeautifulSoup(response.text, "html.parser")
    
    resultados = []
    rodada_atual = None

    rodada_tag = soup.find(string=lambda s: s and "Rodada" in s and any(char.isdigit() for char in s))
    if rodada_tag:
        rodada_atual = rodada_tag.strip()

    jogo_tags = soup.find_all('div', string=lambda s: s and 'x' in s and any(char.isdigit() for char in s))

    for tag in jogo_tags:
        texto = tag.get_text(strip=True)
        if texto.count('x') != 1:
            continue

        try:
            partes = texto.split('x')
            time1 = partes[0].strip()
            time2 = partes[1].strip()

            placar1 = ''.join(filter(str.isdigit, time1))
            placar2 = ''.join(filter(str.isdigit, time2))

            time1_nome = ''.join(filter(lambda c: not c.isdigit(), time1)).strip()
            time2_nome = ''.join(filter(lambda c: not c.isdigit(), time2)).strip()

            resultados.append({
                "rodada": rodada_atual or "Rodada não identificada",
                "time1": time1_nome,
                "time2": time2_nome,
                "placar": f"{placar1}x{placar2}"
            })
        except:
            continue

    return resultados or {"erro": "Nenhum jogo encontrado"}

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

@app.get("/rodada/{campeonato}")
def rodada(campeonato: str):
    nome_map = {
        "brasileirao": "do Brasileirão",
        "libertadores": "da Libertadores",
        "sulamericana": "da Sul-Americana",
        "copadobrasil": "da Copa do Brasil"
    }

    if campeonato not in nome_map:
        return JSONResponse(content={"erro": "Campeonato inválido"}, status_code=400)

    resultados = buscar_resultados_por_campeonato(nome_map[campeonato])
    return resultados
