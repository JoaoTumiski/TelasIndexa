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

        if verificar_primeira_execucao():
            config_window = ConfigIni()
            config_window.show()
            app.exec()

        # ✅ Abre a tela principal, mesmo se estiver offline
        window = ElevatorScreen()
        window.show()

        # ✅ Executa o atualizador sem travar caso falhe
        try:
            subprocess.Popen(["python", "atualizador.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"⚠️ Erro ao iniciar atualizador: {e}")

        sys.exit(app.exec())

    except Exception as e:
        print(f"❌ Erro ao iniciar a aplicação: {e}")
