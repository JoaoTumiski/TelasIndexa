import os
import json
import requests
import time
import sys
import subprocess

BASE_DIR = getattr(sys, '_MEIPASS', os.path.abspath("."))

# Configurações
SERVER_URL = "http://15.228.8.3:8000"
CACHE_DIR = os.path.join(BASE_DIR, "cache")
VERSAO_FILE = os.path.join(CACHE_DIR, "versao.json")  # Caminho do arquivo de versão
CONFIG_PATH = "config.json"

def carregar_config():
    """Carrega o ID do cliente a partir do arquivo config.json"""
    if not os.path.exists(CONFIG_PATH):
        print(f"❌ Arquivo de configuração não encontrado: {CONFIG_PATH}")
        return 102  # Retorna um ID padrão caso não encontre

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            config_data = json.load(file)
            return int(config_data.get("tela_id", 102))  # Retorna 102 se não encontrar
    except Exception as e:
        print(f"❌ Erro ao carregar config.json: {e}")
        return 102  # Retorna um ID padrão caso haja erro

# 🔹 Define o CLIENTE_ID dinamicamente
CLIENTE_ID = carregar_config()
print(f"✅ Cliente ID carregado: {CLIENTE_ID}")  # Debug para garantir que carregou

# Criar a pasta cache caso não exista
os.makedirs(CACHE_DIR, exist_ok=True)

def carregar_versao():
    """Carrega a versão instalada localmente"""
    if os.path.exists(VERSAO_FILE):
        try:
            with open(VERSAO_FILE, "r") as file:
                return json.load(file).get("versao", 1)
        except Exception as e:
            print(f"⚠️ Erro ao ler versão local: {e}")
            return 1
    return 1  # Se o arquivo não existir, assume que está na versão 1

def salvar_versao(nova_versao):
    """Salva a nova versão instalada"""
    try:
        with open(VERSAO_FILE, "w") as file:
            json.dump({"versao": nova_versao}, file)
    except Exception as e:
        print(f"⚠️ Erro ao salvar versão: {e}")

def verificar_atualizacao():
    """Verifica no servidor se há nova versão"""
    try:
        versao_atual = carregar_versao()
        response = requests.get(f"{SERVER_URL}/check-update/{CLIENTE_ID}/{versao_atual}", timeout=10)
        
        if response.status_code == 200 and response.json().get("update_available"):
            nova_versao = response.json()["versao"]
            download_url = response.json()["download_url"]

            print(f"🔄 Nova atualização disponível: {nova_versao}. Baixando...")
            destino_arquivo = os.path.join(CACHE_DIR, f"update_{nova_versao}.zip")

            # ✅ **Baixar o arquivo antes de continuar**
            if baixar_arquivo(download_url, destino_arquivo):
                salvar_versao(nova_versao)
                print("✅ Atualização concluída!")

                # 🔥 **Aguardar para garantir que o arquivo foi salvo corretamente**
                time.sleep(2)

                # 🔥 **Executar `unzip.py` para extrair**
                print(f"📂 Extraindo arquivos da atualização {nova_versao}...")
                subprocess.run(["python", "unzip.py", destino_arquivo])

                # 🔥 **Deletar o ZIP somente após a extração**
                if os.path.exists(destino_arquivo):
                    os.remove(destino_arquivo)
                    print(f"🗑️ Arquivo ZIP {destino_arquivo} removido após extração.")
            else:
                print("❌ Ocorreu um erro ao baixar a atualização.")

        else:
            print("✅ Nenhuma nova atualização disponível.")

    except requests.exceptions.RequestException as e:
        print(f"⚠️ Erro ao conectar ao servidor: {e}")

    except Exception as e:
        print(f"❌ Erro inesperado ao verificar atualização: {e}")

def baixar_arquivo(url, destino):
    """Baixa o arquivo de atualização e verifica se foi baixado corretamente"""
    try:
        response = requests.get(url, stream=True, timeout=15)
        if response.status_code == 200:
            with open(destino, "wb") as file:
                for chunk in response.iter_content(1024 * 1024 * 4):
                    file.write(chunk)

            # ✅ **Verificar se o arquivo realmente existe antes de continuar**
            if os.path.exists(destino):
                print(f"📦 Download concluído: {destino}")
                return True
            else:
                print("❌ Ocorreu um erro no download. Arquivo não encontrado após o download.")
                return False
        else:
            print(f"❌ Erro ao baixar o arquivo. Status: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"⚠️ Erro na requisição de download: {e}")
        return False

    except Exception as e:
        print(f"❌ Erro inesperado ao baixar arquivo: {e}")
        return False

if __name__ == "__main__":
    tempo_espera = 1200  # Tempo inicial de espera (segundos)

    while True:
        try:
            verificar_atualizacao()
            print(f"⏳ Aguardando {tempo_espera // 60} minutos para nova verificação...")
            time.sleep(tempo_espera)

        except Exception as e:
            print(f"❌ Erro inesperado no loop principal: {e}")
            print("🔄 Reiniciando verificação após 30 segundos...")
            time.sleep(30)  # Espera antes de tentar novamente
