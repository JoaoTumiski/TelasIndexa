import os
import json
import requests
from PIL import Image
from config.database import supabase

NEWS_JSON_PATH = "cache/noticias.json"
LOCAL_NEWS_FOLDER = os.path.join("cache", "News")
CONFIG_PATH = "config.json"
S3_BUCKET = "imagens-noticias"
S3_PREFIX = "News/"

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

def obter_noticias_supabase():
    if supabase is None:
        print("⚠️ Supabase não disponível. Pulando atualização de notícias.")
        return None, None
    try:
        response = supabase.table("noticias").select("valor, atualizado_em").eq("tipo", "noticias").execute()
        if response.data:
            data = response.data[0]
            noticias = data["valor"]
            atualizado_em = data["atualizado_em"]
            if isinstance(noticias, str):
                noticias = json.loads(noticias)
            return noticias, atualizado_em
    except Exception as e:
        print(f"❌ Erro ao buscar notícias no Supabase: {e}")
    return None, None

def carregar_noticias_local():
    if not os.path.exists(NEWS_JSON_PATH):
        return None, None
    try:
        with open(NEWS_JSON_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data.get("noticias"), data.get("atualizado_em")
    except Exception as e:
        print(f"❌ Erro ao carregar notícias locais: {e}")
        return None, None

def salvar_noticias_localmente(noticias, atualizado_em):
    try:
        with open(NEWS_JSON_PATH, "w", encoding="utf-8") as file:
            json.dump({"noticias": noticias, "atualizado_em": atualizado_em}, file, indent=4, ensure_ascii=False)
        print(f"✅ Notícias salvas em {NEWS_JSON_PATH}")
    except Exception as e:
        print(f"❌ Erro ao salvar notícias localmente: {e}")

def limpar_imagens_antigas_local():
    if not os.path.exists(LOCAL_NEWS_FOLDER):
        print("⚠️ Pasta de notícias ainda não existe. Pulando limpeza.")
        return
    for filename in os.listdir(LOCAL_NEWS_FOLDER):
        file_path = os.path.join(LOCAL_NEWS_FOLDER, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"🗑️ Imagem local removida: {file_path}")
        except Exception as e:
            print(f"⚠️ Erro ao remover {file_path}: {e}")

def verificar_imagem_valida(path):
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception as e:
        print(f"❌ Imagem inválida ou corrompida: {path} — {e}")
        return False

def baixar_imagens_noticias_s3(noticias):
    if not noticias:
        print("⚠️ Nenhuma notícia para processar imagens.")
        return

    os.makedirs(LOCAL_NEWS_FOLDER, exist_ok=True)
    imagens_validas = 0

    for origem in noticias:
        for noticia in noticias[origem]:
            nome_imagem = noticia.get("imagem")
            if not nome_imagem:
                continue

            url = f"https://{S3_BUCKET}.s3.sa-east-1.amazonaws.com/{S3_PREFIX}{nome_imagem}"
            local_path = os.path.join(LOCAL_NEWS_FOLDER, nome_imagem)

            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    with open(local_path, "wb") as f:
                        f.write(response.content)
                    print(f"📥 Imagem baixada: {nome_imagem}")

                    if verificar_imagem_valida(local_path):
                        imagens_validas += 1
                    else:
                        os.remove(local_path)
                        print(f"🗑️ Imagem inválida: {nome_imagem}")
                else:
                    print(f"⚠️ Erro {response.status_code} ao baixar {url}")
            except Exception as e:
                print(f"❌ Falha ao baixar {nome_imagem}: {e}")

    print(f"✅ {imagens_validas} imagens válidas baixadas com sucesso.")

def verificar_e_atualizar_noticias():
    print("🔄 Verificando atualização das notícias...")

    noticias_local, timestamp_local = carregar_noticias_local()
    noticias_supabase, timestamp_supabase = obter_noticias_supabase()

    if not noticias_supabase:
        print("⚠️ Nenhuma notícia disponível no Supabase. Mantendo a versão local.")
        return noticias_local

    if timestamp_supabase != timestamp_local:
        print(f"🆕 Atualização detectada! Novo timestamp: {timestamp_supabase}")
        limpar_imagens_antigas_local()
        baixar_imagens_noticias_s3(noticias_supabase)
        salvar_noticias_localmente(noticias_supabase, timestamp_supabase)
        return noticias_supabase

    print("✅ Notícias já estão atualizadas. Nenhuma ação necessária.")
    return noticias_local
