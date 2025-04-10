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

def baixar_videos_ausentes(json_data):
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
                else:
                    print(f"⚠️ Erro ao baixar {caminho_s3}: Status {response.status_code}")
            except Exception as e:
                print(f"❌ Erro inesperado ao baixar {caminho_s3}: {e}")

def deletar_videos_entretenimento(json_data):
    print("🗑️ Verificando vídeos para exclusão...")
    arquivos_json = set(item["video"] for item in json_data.get("entretenimento", []) if item.get("status") != "deleted")
    print(f"📦 Arquivos válidos no JSON: {arquivos_json}")

    for root, _, files in os.walk(ENTRETENIMENTO_DIR):
        for file in files:
            caminho_relativo = os.path.relpath(os.path.join(root, file), ENTRETENIMENTO_DIR).replace("\\", "/")
            if caminho_relativo not in arquivos_json:
                try:
                    os.remove(os.path.join(ENTRETENIMENTO_DIR, caminho_relativo))
                    print(f"🗑️ Arquivo de entretenimento deletado: {caminho_relativo}")
                except Exception as e:
                    print(f"⚠️ Erro ao deletar {caminho_relativo}: {e}")

def verificar_atualizacao_entretenimento():
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

        # 🔥 Sempre salva o JSON
        with open(os.path.join(CACHE_DIR, "entretenimento_update.json"), "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        # 🔍 Verifica se há vídeos ausentes
        faltando = False
        for item in json_data.get("entretenimento", []):
            if item.get("status") == "deleted":
                continue

            caminho_s3 = item.get("video")
            caminho_local = os.path.join(ENTRETENIMENTO_DIR, caminho_s3)
            if not os.path.exists(caminho_local):
                faltando = True
                print(f"⚠️ Vídeo ausente: {caminho_s3}")

        # 🔄 Só executa ações se versão for nova OU arquivos faltarem
        if versao_remota > versao_local or faltando:
            print("🔁 Iniciando sincronização de entretenimento...")
            baixar_videos_ausentes(json_data)
            deletar_videos_entretenimento(json_data)

            if versao_remota > versao_local:
                salvar_versao_entretenimento(versao_remota)
                print(f"✅ Versão local atualizada para {versao_remota}")
        else:
            print("✅ Nenhuma atualização necessária. Todos os arquivos estão presentes.")

        print("✅ Processo de atualização de entretenimento finalizado.")

    except Exception as e:
        print(f"❌ Erro ao verificar atualização de entretenimento: {e}")


