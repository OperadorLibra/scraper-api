from fastapi import FastAPI
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import re
import os

# Configuração da API
app = FastAPI(
    title="API de Placares de Jogos",
    description="API para buscar placares de jogos de futebol",
    version="1.0.0"
)

class Jogo(BaseModel):
    time1: str
    time2: str

class ListaJogos(BaseModel):
    jogos: list[Jogo]

def buscar_placar(time1, time2):
    query = f"{time1} x {time2} site:ge.globo.com"
    url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        match = re.search(r"(\d+)\s*x\s*(\d+)", soup.text)
        if match:
            return f"{match.group(1)}x{match.group(2)}"
        return "Placar não encontrado"
    except Exception as e:
        return f"Erro ao buscar placar: {str(e)}"

@app.get("/")
async def root():
    return {
        "mensagem": "API de Placares de Jogos - Use a rota /placares para buscar placares",
        "documentação": "Acesse /docs para ver a documentação completa da API"
    }

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

# Para garantir que a API funcione no Render
if __name__ == "__main__":
    import uvicorn
    # Pega a porta do ambiente ou usa 8000 como padrão
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("scraper_api:app", host="0.0.0.0", port=port)
