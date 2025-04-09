import os
import time
import json
import requests
import subprocess
import atexit
import zipfile
import sys
from config.database import supabase

BASE_DIR = os.path.abspath(".")
CACHE_DIR = os.path.join(BASE_DIR, "cache")
VERSAO_FILE = os.path.join(CACHE_DIR, "versao_software.json")
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
LOCKFILE = os.path.join(CACHE_DIR, "software_updater.lock")

os.makedirs(CACHE_DIR, exist_ok=True)

def carregar_config():
    if not os.path.exists(CONFIG_PATH):
        return 101
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
            return int(data.get("tela_id", 101))
    except:
        return 101

def carregar_versao_local():
    if not os.path.exists(VERSAO_FILE):
        return 1
    try:
        with open(VERSAO_FILE, "r") as f:
            return json.load(f).get("versao", 1)
    except:
        return 1

def salvar_versao_local(versao):
    try:
        with open(VERSAO_FILE, "w") as f:
            json.dump({"versao": versao}, f)
    except:
        pass

def limpar_lockfile():
    if os.path.exists(LOCKFILE):
        os.remove(LOCKFILE)

def baixar_arquivo(url, destino):
    try:
        r = requests.get(url, stream=True, timeout=15)
        if r.status_code == 200:
            with open(destino, "wb") as f:
                for chunk in r.iter_content(1024 * 1024):
                    f.write(chunk)
            return True
    except:
        pass
    return False

def extrair_zip(zip_path, destino="."):
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(destino)
        return True
    except:
        return False

def verificar_nova_versao():
    cliente_id = carregar_config()
    versao_instalada = carregar_versao_local()

    if not os.path.exists(VERSAO_FILE):
        salvar_versao_local(versao_instalada)

    try:
        response = supabase.table("sistema_update").select("*").eq("cliente_id", cliente_id).execute()
        dados = response.data[0] if response.data else None
        if not dados:
            return

        versao_disponivel = dados.get("versao_disponivel")
        url_download = dados.get("download_url")

        if versao_disponivel > versao_instalada:
            zip_path = os.path.join(BASE_DIR, f"software_v{versao_disponivel}.zip")

            if baixar_arquivo(url_download, zip_path):
                if extrair_zip(zip_path, BASE_DIR):
                    salvar_versao_local(versao_disponivel)
                    os.remove(zip_path)
                    # ✅ Atualiza no Supabase
                    supabase.table("sistema_update").update({
                        "versao_instalada": versao_disponivel,
                        "atualizado": True
                    }).eq("cliente_id", cliente_id).execute()

                    # 🧨 Encerra instância atual do app.py, se estiver rodando
                    import psutil
                    for proc in psutil.process_iter(["pid", "cmdline"]):
                        if proc.info["cmdline"] and "app.py" in " ".join(proc.info["cmdline"]):
                            try:
                                proc.terminate()
                                proc.wait(timeout=5)
                            except:
                                proc.kill()

                    # 🔁 Reinicia o app.py
                    app_path = os.path.join(BASE_DIR, "app.py")
                    if os.path.exists(app_path):
                        subprocess.Popen([sys.executable, app_path], creationflags=subprocess.CREATE_NO_WINDOW)

                    # Encerra o verificador
                    os._exit(0)

    except:
        pass

if __name__ == "__main__":
    if os.path.exists(LOCKFILE):
        try:
            with open(LOCKFILE, "r") as f:
                pid = int(f.read())
            import psutil
            if psutil.pid_exists(pid):
                sys.exit(0)
            else:
                os.remove(LOCKFILE)
        except:
            os.remove(LOCKFILE)

    with open(LOCKFILE, "w") as f:
        f.write(str(os.getpid()))

    atexit.register(limpar_lockfile)

    while True:
        verificar_nova_versao()
        time.sleep(1200)  # 20 minutos
