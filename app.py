import os
import sys
import subprocess
from PyQt6.QtWidgets import QApplication
from config_ini import ConfigIni
from main_window import ElevatorScreen

CONFIG_FILE = "config.json"

# 🔇 Suprime logs do FFmpeg enviados ao stderr
sys.stderr = open(os.devnull, 'w')

# 🔧 Desativa debug de ffmpeg do Qt
os.environ["QT_LOGGING_RULES"] = "qt.multimedia.ffmpeg.debug=false"

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
            subprocess.Popen(["python", atualizador_path])
        except Exception as e:
            print(f"⚠️ Erro ao iniciar atualizador: {e}")

        window = ElevatorScreen()
        window.show()

        sys.exit(app.exec())

    except Exception as e:
        print(f"❌ Erro ao iniciar a aplicação: {e}")


