import sys
import os
import subprocess
from PyQt6.QtWidgets import QApplication
from config_ini import ConfigIni
from main_window import ElevatorScreen

CONFIG_FILE = "config.json"

def verificar_primeira_execucao():
    """Verifica se o ID da Tela já foi salvo"""
    return not os.path.exists(CONFIG_FILE)

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)

        if verificar_primeira_execucao():
            # 🔹 Primeira execução: mostrar tela de configuração
            config_window = ConfigIni()
            config_window.show()
            app.exec()  # Espera o usuário salvar antes de continuar

        # 🔹 Após salvar o ID, inicia o software normalmente
        window = ElevatorScreen()
        window.show()

        # 🔹 Inicia o atualizador em segundo plano
        subprocess.Popen(["python", "atualizador.py"])

        sys.exit(app.exec())

    except Exception as e:
        print(f"❌ Erro ao iniciar a aplicação: {e}")
