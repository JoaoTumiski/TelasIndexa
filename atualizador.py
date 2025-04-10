import os
import atexit
import time
import sys
import psutil

from atualizadores import sistema, entretenimento

BASE_DIR = getattr(sys, '_MEIPASS', os.path.abspath("."))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
LOCKFILE = os.path.join(CACHE_DIR, "atualizador.lock")

os.makedirs(CACHE_DIR, exist_ok=True)

def limpar_lockfile():
    if os.path.exists(LOCKFILE):
        os.remove(LOCKFILE)

if __name__ == "__main__":
    tempo_espera = 1200  # 20 minutos

    # Verifica se já está rodando
    if os.path.exists(LOCKFILE):
        try:
            with open(LOCKFILE, "r") as f:
                pid = int(f.read())
            if psutil.pid_exists(pid):
                print("🚫 O atualizador já está em execução (processo ativo). Abortando.")
                sys.exit(0)
            else:
                print("⚠️ Lockfile encontrado, mas processo inativo. Limpando lockfile antigo.")
                os.remove(LOCKFILE)
        except Exception as e:
            print(f"⚠️ Erro ao validar lockfile: {e}. Limpando mesmo assim.")
            os.remove(LOCKFILE)

    with open(LOCKFILE, "w") as f:
        f.write(str(os.getpid()))

    atexit.register(limpar_lockfile)

    # 🔁 Loop principal de verificação
    while True:
        try:
            print("\n🧪 Verificando atualizações gerais do sistema...")
            sistema.verificar_atualizacao()

            print("🎞️ Verificando atualizações de entretenimento...")
            entretenimento.verificar_atualizacao_entretenimento()

            print("✅ Fim do ciclo. Aguardando próximo...")
            time.sleep(tempo_espera)

        except Exception as e:
            print(f"❌ Erro inesperado no loop principal: {e}")
            print("⏳ Aguardando 30s antes de tentar novamente...")
            time.sleep(30)
