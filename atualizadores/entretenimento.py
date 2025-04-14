import os
import json
import requests
from config.database import supabase
import boto3

BASE_DIR = getattr(__builtins__, '_MEIPASS', os.path.abspath("."))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
ENTRETENIMENTO_DIR = os.path.join(CACHE_DIR, "Entretenimento")
ENTRETENIMENTO_VERSAO_FILE = os.path.join(CACHE_DIR, "versao_entretenimento.json")

s3 = boto3.client('s3', region_name='sa-east-1')
os.makedirs(ENTRETENIMENTO_DIR, exist_ok=True)

def carregar_versao_entretenimento():
    if os.path.exists(ENTRETENIMENTO_VERSAO_FILE):
        try:
            with open(ENTRETENIMENTO_VERSAO_FILE, "r") as f:
                return json.load(f).get("versao", 0)
        except:
            return 0
    return 0

def salvar_versao_entretenimento(versao):
    with open(ENTRETENIMENTO_VERSAO_FILE, "w") as f:
        json.dump({"versao": versao}, f)

def baixar_videos_ausentes(json_data, callback=None):
    print("📁 Iniciando download de vídeos ausentes...")
    for item in json_data.get("entretenimento", []):
        if item.get("status") == "deleted":
            continue

        caminho_s3 = item.get("video")
        caminho_local = os.path.join(ENTRETENIMENTO_DIR, caminho_s3)

        if not os.path.exists(caminho_local):
            print(f"⬇️ Baixando novo vídeo: {caminho_s3}")
            try:
                url = f"https://videos-entretenimento.s3.sa-east-1.amazonaws.com/{caminho_s3}"
                response = requests.get(url, stream=True, timeout=15)
                if response.status_code == 200:
                    os.makedirs(os.path.dirname(caminho_local), exist_ok=True)
                    with open(caminho_local, "wb") as f:
                        for chunk in response.iter_content(1024 * 1024 * 2):
                            f.write(chunk)
                    print(f"✅ Baixado com sucesso: {caminho_s3}")
                    if callback:
                        callback()
                else:
                    print(f"⚠️ Erro ao baixar {caminho_s3}: Status {response.status_code}")
            except Exception as e:
                print(f"❌ Erro inesperado ao baixar {caminho_s3}: {e}")

def deletar_videos_entretenimento(json_data):
    print("🗑️ Verificando vídeos para exclusão...")

    arquivos_validos = set()
    arquivos_deletar = set()

    for item in json_data.get("entretenimento", []):
        caminho = item.get("video")
        status = item.get("status")
        if not caminho:
            continue
        if status == "deleted":
            arquivos_deletar.add(os.path.normpath(caminho))
        else:
            arquivos_validos.add(os.path.normpath(caminho))

    for root, _, files in os.walk(ENTRETENIMENTO_DIR):
        for file in files:
            caminho_rel = os.path.relpath(os.path.join(root, file), ENTRETENIMENTO_DIR).replace("\\", "/")
            caminho_norm = os.path.normpath(caminho_rel)
            caminho_completo = os.path.join(ENTRETENIMENTO_DIR, caminho_norm)

            if caminho_norm in arquivos_deletar or caminho_norm not in arquivos_validos:
                try:
                    os.remove(caminho_completo)
                    print(f"🗑️ Arquivo de entretenimento deletado: {caminho_rel}")
                except Exception as e:
                    print(f"⚠️ Erro ao deletar {caminho_rel}: {e}")

def contar_videos_faltando():
    response = supabase.table("entretenimento_updates").select("json_data").order("versao", desc=True).limit(1).execute()
    if not response.data:
        return 0
    json_data = response.data[0]["json_data"]
    return sum(1 for item in json_data.get("entretenimento", []) if item.get("status") != "deleted" and not os.path.exists(os.path.join(ENTRETENIMENTO_DIR, item["video"])))


def verificar_atualizacao_entretenimento(callback=None):
    versao_local = carregar_versao_entretenimento()
    try:
        response = supabase.table("entretenimento_updates")\
            .select("versao, json_data")\
            .order("versao", desc=True).limit(1).execute()

        dados = response.data[0] if response.data else None
        if not dados:
            return

        versao_remota = dados["versao"]
        json_data = dados["json_data"]
        print(f"📡 Versão local: {versao_local}")
        print(f"📥 Versão remota: {versao_remota}")

        with open(os.path.join(CACHE_DIR, "entretenimento_update.json"), "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        # Verifica se há vídeos faltando
        faltando = any(
            item.get("status") != "deleted" and
            not os.path.exists(os.path.join(ENTRETENIMENTO_DIR, item["video"]))
            for item in json_data.get("entretenimento", [])
        )

        if versao_remota > versao_local or faltando:
            print("🔁 Iniciando sincronização de entretenimento...")
            baixar_videos_ausentes(json_data, callback=callback)
            deletar_videos_entretenimento(json_data)
            if versao_remota > versao_local:
                salvar_versao_entretenimento(versao_remota)
                print(f"✅ Versão local atualizada para {versao_remota}")
        else:
            print("✅ Nenhuma atualização necessária. Todos os arquivos estão presentes.")

        print("✅ Processo de atualização de entretenimento finalizado.")
    except Exception as e:
        print(f"❌ Erro ao verificar atualização de entretenimento: {e}")
