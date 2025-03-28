import os
import sys
import zipfile
import json
import time  # 📌 Adicionado para aguardar antes de processar

BASE_DIR = getattr(sys, '_MEIPASS', os.path.abspath("."))
CACHE_DIR = os.path.join(BASE_DIR, "cache")

def extrair_zip(zip_path):
    """Extrai os arquivos do ZIP para a pasta cache"""
    if not os.path.exists(zip_path):
        print(f"❌ Arquivo ZIP {zip_path} não encontrado! Aguardando 2 segundos...")
        time.sleep(2)  # ✅ Aguarde um pouco antes de continuar
        if not os.path.exists(zip_path):
            print(f"❌ Arquivo ZIP ainda não encontrado após 2 segundos. Abortando extração.")
            return
    
    # ✅ Extrai os arquivos do ZIP
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(CACHE_DIR)

    print(f"📂 Arquivos extraídos para {CACHE_DIR}")

    # ✅ Verifica se o `update.json` existe
    update_json_path = os.path.join(CACHE_DIR, "update.json")
    if os.path.exists(update_json_path):
        processar_json(update_json_path)
    else:
        print("⚠️ Arquivo `update.json` não encontrado no ZIP. Nenhum arquivo foi deletado.")

def processar_json(json_path):
    """Processa o update.json para deletar arquivos marcados como 'deleted'"""
    try:
        with open(json_path, "r") as file:
            update_data = json.load(file)

        categorias = {
            "Entretenimento": "video",
            "Propagandas": "video",
            "Banners": "imagem",
            "CondominiumNotices": "mensagem",
            "News": "imagem"
        }


        for categoria, chave in categorias.items():
            if categoria in update_data:
                for item in update_data[categoria]:
                    if item.get("status") == "deleted":
                        caminho_relativo = item.get(chave)  # 🔹 Pega o caminho correto para cada categoria
                        if caminho_relativo:
                            caminho_arquivo = os.path.join(CACHE_DIR, caminho_relativo)
                            if os.path.exists(caminho_arquivo):
                                os.remove(caminho_arquivo)
                                print(f"🗑️ Arquivo deletado: {caminho_arquivo}")
                            else:
                                print(f"⚠️ Arquivo para deletar não encontrado: {caminho_arquivo}")

    except Exception as e:
        print(f"❌ Erro ao processar o update.json: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Nenhum arquivo ZIP especificado!")
    else:
        zip_path = sys.argv[1]
        extrair_zip(zip_path)
