import os
import sys
import subprocess
import atexit
os.environ["QT_LOGGING_RULES"] = "qt.multimedia.ffmpeg.debug=false"
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication 
from config_ini import ConfigIni
from main_window import ElevatorScreen

CONFIG_FILE = "config.json"
atualizador_proc = None

def verificar_primeira_execucao():
    return not os.path.exists(CONFIG_FILE)

def encerrar_atualizador():
    if atualizador_proc and atualizador_proc.poll() is None:
        print("🛑 Encerrando atualizador...")
        atualizador_proc.terminate()
        try:
            atualizador_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            atualizador_proc.kill()

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        primeira_vez = verificar_primeira_execucao()

        if primeira_vez:
            config_window = ConfigIni()
            config_window.show()
            app.exec()

        # ✅ Sempre executa o atualizador
        try:
            atualizador_path = os.path.join(os.path.dirname(__file__), "atualizador.py")
            print("🚀 Iniciando atualizador:", atualizador_path)
            atualizador_proc = subprocess.Popen(
                [sys.executable, atualizador_path],
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            QCoreApplication.instance().aboutToQuit.connect(encerrar_atualizador)
            atexit.register(encerrar_atualizador)

        except Exception as e:
            print(f"⚠️ Erro ao iniciar atualizador: {e}")

        window = ElevatorScreen()
        window.show()

        sys.exit(app.exec())

    except Exception as e:
        print(f"❌ Erro ao iniciar a aplicação: {e}")
