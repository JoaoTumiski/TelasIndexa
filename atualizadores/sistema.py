import sys
import os
import json
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.database import supabase
import requests

BASE_DIR = getattr(__builtins__, '_MEIPASS', os.path.abspath("."))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
UPDATE_JSON_FILE = os.path.join(CACHE_DIR, "update.json")
CONFIG_PATH = "config.json"
S3_BASE_URL = "https://telas-clientes.s3.sa-east-1.amazonaws.com"

os.makedirs(CACHE_DIR, exist_ok=True)

def carregar_config():
    if not os.path.exists(CONFIG_PATH):
        return 101
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            config_data = json.load(file)
            return int(config_data.get("tela_id", 101))
    except:
        return 101

CLIENTE_ID = carregar_config()

def baixar_arquivo(url, destino, tentativas=3):
    for tentativa in range(1, tentativas + 1):
        try:
            response = requests.get(url, stream=True, timeout=20)
            if response.status_code == 200:
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                with open(destino, "wb") as file:
                    for chunk in response.iter_content(1024 * 1024 * 4):
                        file.write(chunk)
                return os.path.exists(destino)
        except:
            time.sleep(3)
    return False

def verificar_integridade_arquivos(json_data):
    arquivos_faltando = []
    for categoria in ["Propagandas", "Banners", "CondominiumNotices"]:
        for item in json_data.get(categoria, []):
            if item.get("status") == "deleted":
                continue
            caminho = item.get("video") if categoria == "Propagandas" else item.get("imagem") if categoria == "Banners" else item.get("mensagem")
            if not caminho:
                continue
            caminho_local = os.path.join(CACHE_DIR, caminho)
            if not os.path.exists(caminho_local):
                arquivos_faltando.append((categoria, caminho))
    return arquivos_faltando

def contar_arquivos_faltando():
    response = supabase.table("updates_clientes").select("json_data").eq("cliente_id", CLIENTE_ID).limit(1).execute()
    if not response.data:
        return 0
    json_data = response.data[0]["json_data"]
    return len(verificar_integridade_arquivos(json_data))

def baixar_arquivos_faltando(arquivos, pasta_s3, callback=None):
    if not pasta_s3:
        return
    for _, caminho in arquivos:
        url = f"{S3_BASE_URL}/{pasta_s3}/{caminho}"
        destino = os.path.join(CACHE_DIR, caminho)
        if baixar_arquivo(url, destino) and callback:
            callback()

def deletar_arquivos_removidos(json_data):
    print("🗑️ Verificando e removendo arquivos obsoletos...")

    categorias = {
        "Propagandas": "video",
        "Banners": "imagem",
        "CondominiumNotices": "mensagem"
    }

    arquivos_validos = set()
    for categoria, chave in categorias.items():
        for item in json_data.get(categoria, []):
            caminho = item.get(chave)
            if caminho and item.get("status") != "deleted":
                caminho_absoluto = os.path.normpath(os.path.join(CACHE_DIR, caminho))
                arquivos_validos.add(caminho_absoluto)

    for categoria, chave in categorias.items():
        pasta = os.path.join(CACHE_DIR, categoria)
        if not os.path.exists(pasta):
            continue
        for root, _, files in os.walk(pasta):
            for file in files:
                caminho_absoluto = os.path.normpath(os.path.join(root, file))
                if caminho_absoluto not in arquivos_validos:
                    try:
                        os.remove(caminho_absoluto)
                        print(f"🗑️ Arquivo removido: {caminho_absoluto}")
                    except Exception as e:
                        print(f"⚠️ Falha ao remover {caminho_absoluto}: {e}")


def verificar_atualizacao(callback=None):
    try:
        response = supabase.table("updates_clientes").select("json_data").eq("cliente_id", CLIENTE_ID).limit(1).execute()
        if response.data:
            json_data = response.data[0]["json_data"]
            with open(UPDATE_JSON_FILE, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)
            arquivos_faltando = verificar_integridade_arquivos(json_data)
            if arquivos_faltando:
                baixar_arquivos_faltando(arquivos_faltando, json_data.get("pasta_s3"), callback=callback)
            deletar_arquivos_removidos(json_data)
    except:
        pass

if __name__ == "__main__":
    while True:
        verificar_atualizacao()
        time.sleep(1200)
