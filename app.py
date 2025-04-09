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

# Substitua essa parte no app.py
atualizador_path = os.path.join(os.path.dirname(__file__), "atualizador.py")
verificador_path = os.path.join(os.path.dirname(__file__), "verificador_sistema.py")

def verificar_primeira_execucao():
    return not os.path.exists(CONFIG_FILE)

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
            creationflags=subprocess.CREATE_NO_WINDOW)

            verificador_proc = subprocess.Popen(
            [sys.executable, verificador_path],
            creationflags=subprocess.CREATE_NO_WINDOW)

            # Encerrar ambos os subprocessos ao sair
            def encerrar_processos():
                for proc in [atualizador_proc, verificador_proc]:
                    if proc and proc.poll() is None:
                        print("🛑 Encerrando subprocesso...")
                        proc.terminate()
                        try:
                            proc.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            proc.kill()

            QCoreApplication.instance().aboutToQuit.connect(encerrar_processos)
            atexit.register(encerrar_processos)

        except Exception as e:
            print(f"⚠️ Erro ao iniciar atualizador: {e}")

        window = ElevatorScreen()
        window.show()

        sys.exit(app.exec())

    except Exception as e:
        print(f"❌ Erro ao iniciar a aplicação: {e}")
