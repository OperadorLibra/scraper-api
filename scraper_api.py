from fastapi import FastAPI
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import re

app = FastAPI()

class Jogo(BaseModel):
    time1: str
    time2: str

class ListaJogos(BaseModel):
    jogos: list[Jogo]

def buscar_placar(time1, time2):
    query = f"{time1} x {time2} site:ge.globo.com"
    url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    match = re.search(r"(\d+)\s*x\s*(\d+)", soup.text)
    if match:
        return f"{match.group(1)}x{match.group(2)}"
    return "Placar não encontrado"

@app.post("/placares")
async def obter_placares(lista: ListaJogos):
    resultados = []
    for jogo in lista.jogos:
        placar = buscar_placar(jogo.time1, jogo.time2)
        resultados.append({
            "time1": jogo.time1,
            "time2": jogo.time2,
            "placar": placar
        })
    return {"resultados": resultados}
