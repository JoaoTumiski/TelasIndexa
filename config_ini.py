import sys
import os
import json
import subprocess
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QLineEdit
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer, QCoreApplication

CONFIG_FILE = "config.json"
EXTRACT_PATH = "cache"  # Pasta onde os arquivos extraídos serão armazenados
atualizador_proc = None

class ConfigIni(QMainWindow):
    def __init__(self):
        super().__init__()

        # Configurações da Janela
        self.setWindowTitle("Configuração Inicial")
        self.setGeometry(100, 100, 800, 600)

        # Carregar e redimensionar a imagem de fundo
        self.background_label = QLabel(self)
        pixmap = QPixmap("assets/background.png")
        pixmap = pixmap.scaled(self.width(), self.height(), Qt.AspectRatioMode.KeepAspectRatioByExpanding)
        self.background_label.setPixmap(pixmap)
        self.background_label.setScaledContents(True)
        self.background_label.setGeometry(0, 0, self.width(), self.height())

        # Campo de texto para o ID da Tela
        self.text_input = QLineEdit(self)
        self.text_input.setPlaceholderText("Digite o ID da Tela")
        self.text_input.setGeometry(300, 250, 200, 40)

        # Botão de salvar
        self.button = QPushButton("Salvar", self)
        self.button.setGeometry(350, 300, 100, 40)
        self.button.clicked.connect(self.salvar_config)

        # Mensagem de status
        self.status_label = QLabel("", self)
        self.status_label.setGeometry(250, 350, 300, 40)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 18px; text-align: center; color: white;")

        # Ajustar a ordem dos elementos
        self.text_input.raise_()
        self.button.raise_()
        self.status_label.raise_()

        # Redimensionamento dinâmico
        self.resizeEvent = self.on_resize

        # Timer para verificar a existência do arquivo JSON a cada 3 segundos
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self.verificar_json_criado)


    def encerrar_atualizador(self):
        global atualizador_proc
        if atualizador_proc and atualizador_proc.poll() is None:
            print("🛑 Encerrando atualizador...")
            try:
                atualizador_proc.terminate()
                atualizador_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                atualizador_proc.kill()

    def salvar_config(self):
        """Salva o ID da Tela, exibe mensagem e inicia atualização"""
        entrada = self.text_input.text().strip()  # Ex: "101_1" ou "101"
        
        if entrada:
            partes = entrada.split("_")
            cliente_id = partes[0]
            modelo_tela = int(partes[1]) if len(partes) > 1 and partes[1].isdigit() else 0
            
            config = {
                "tela_id": cliente_id,
                "modelo": modelo_tela
            }

            # Salvar ID e modelo no config.json
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f)

            # Atualizar status e desativar botão
            self.status_label.setText("📡 Fazendo download dos arquivos...")
            self.button.setEnabled(False)
            self.text_input.setEnabled(False)

            # Iniciar atualização e extração
            global atualizador_proc
            atualizador_proc = subprocess.Popen(
            [sys.executable, "atualizador.py"],
            creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.Popen(["python", "unzip.py"])

            # Iniciar o timer para verificar se o JSON foi criado
            self.check_timer.start(3000)  # Verifica a cada 3 segundos
            QCoreApplication.instance().aboutToQuit.connect(self.encerrar_atualizador)

    def verificar_json_criado(self):
        """Verifica se o arquivo <id_da_tela>.json foi criado"""
        json_path = os.path.join(EXTRACT_PATH, "update.json")
        if os.path.exists(json_path):
            self.finalizar_config()  # Se o arquivo existe, inicia o app

    def finalizar_config(self):
        """Fecha a janela e inicia a aplicação"""
        self.status_label.setText("✅ Arquivos baixados e extraídos!")

        # Iniciar a tela principal (sistema.py)
        subprocess.Popen(["python", "sistema.py"])

        # Parar o timer e fechar a janela
        self.check_timer.stop()
        self.close()

    def on_resize(self, event):
        """Redimensiona o background ao ajustar a tela."""
        pixmap = QPixmap("assets/background.png")
        pixmap = pixmap.scaled(self.width(), self.height(), Qt.AspectRatioMode.KeepAspectRatioByExpanding)
        self.background_label.setPixmap(pixmap)
        self.background_label.setGeometry(0, 0, self.width(), self.height())

# 🔹 Teste isolado
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConfigIni()
    window.show()
    sys.exit(app.exec())
