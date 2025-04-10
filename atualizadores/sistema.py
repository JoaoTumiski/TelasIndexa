import os
import json
import time
import subprocess
import requests

BASE_DIR = getattr(__builtins__, '_MEIPASS', os.path.abspath("."))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
VERSAO_FILE = os.path.join(CACHE_DIR, "versao.json")
CONFIG_PATH = "config.json"
SERVER_URL = "http://15.228.8.3:8000"

def carregar_config():
    if not os.path.exists(CONFIG_PATH):
        return 101
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            config_data = json.load(file)
            return int(config_data.get("tela_id", 101))
    except Exception:
        return 101

CLIENTE_ID = carregar_config()

def carregar_versao():
    if os.path.exists(VERSAO_FILE):
        try:
            with open(VERSAO_FILE, "r") as file:
                return json.load(file).get("versao", 1)
        except:
            return 1
    return 1

def salvar_versao(nova_versao):
    try:
        with open(VERSAO_FILE, "w") as file:
            json.dump({"versao": nova_versao}, file)
    except Exception as e:
        print(f"⚠️ Erro ao salvar nova versão: {e}")

def baixar_arquivo(url, destino, tentativas=3):
    for tentativa in range(1, tentativas + 1):
        try:
            print(f"⬇️ Tentando baixar arquivo (tentativa {tentativa})...")
            response = requests.get(url, stream=True, timeout=20)
            if response.status_code == 200:
                with open(destino, "wb") as file:
                    for chunk in response.iter_content(1024 * 1024 * 4):
                        file.write(chunk)
                print("✅ Download concluído.")
                return True
            else:
                print(f"⚠️ Erro HTTP {response.status_code} ao baixar o arquivo.")
        except Exception as e:
            print(f"⚠️ Falha ao tentar baixar (tentativa {tentativa}): {e}")
            time.sleep(3)  # Pequeno atraso antes de tentar novamente
    return False

def verificar_atualizacao():
    try:
        versao_atual = carregar_versao()
        print(f"🔍 Verificando atualizações para a versão {versao_atual}...")

        try:
            response = requests.get(f"{SERVER_URL}/check-update/{CLIENTE_ID}/{versao_atual}", timeout=10)
        except Exception as e:
            print(f"⚠️ Falha na verificação com o servidor: {e}")
            return

        if response.status_code == 200 and response.json().get("update_available"):
            nova_versao = response.json()["versao"]
            download_url = response.json()["download_url"]
            destino_arquivo = os.path.join(CACHE_DIR, f"update_{nova_versao}.zip")

            print(f"🆕 Atualização detectada: {nova_versao}. Baixando ZIP...")

            if baixar_arquivo(download_url, destino_arquivo):
                print("📦 Extraindo atualização...")
                resultado = subprocess.run(
                    ["python", "unzip.py", destino_arquivo],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

                if resultado.returncode == 0:
                    print("✅ Atualização aplicada com sucesso.")
                    salvar_versao(nova_versao)

                    try:
                        requests.post(f"{SERVER_URL}/confirm-update/{CLIENTE_ID}", timeout=10)
                    except Exception as e:
                        print(f"⚠️ Erro ao confirmar atualização com o servidor: {e}")
                else:
                    print("❌ Falha ao extrair atualização. Versão não será marcada como concluída.")

                if os.path.exists(destino_arquivo):
                    os.remove(destino_arquivo)
                    print(f"🧹 ZIP removido: {destino_arquivo}")
            else:
                print("❌ Não foi possível baixar a atualização após várias tentativas.")
        else:
            print("✅ Nenhuma atualização necessária.")
    except Exception as e:
        print(f"❌ Erro inesperado ao verificar atualização: {e}")
