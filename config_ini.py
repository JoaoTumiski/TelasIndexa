import sys
import os
import json
import atexit
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QLineEdit, QProgressBar
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer, QCoreApplication
from update_controller import executar_atualizacoes
from threading import Thread

CONFIG_FILE = "config.json"
EXTRACT_PATH = "cache"  # Pasta onde os arquivos extraídos serão armazenados

class ConfigIni(QMainWindow):
    def __init__(self):
        super().__init__()

        # Configurações da Janela
        self.setWindowTitle("Configuração Inicial")
        self.setGeometry(100, 100, 800, 600)

        # Fundo
        self.background_label = QLabel(self)
        pixmap = QPixmap("assets/background.png")
        pixmap = pixmap.scaled(self.width(), self.height(), Qt.AspectRatioMode.KeepAspectRatioByExpanding)
        self.background_label.setPixmap(pixmap)
        self.background_label.setScaledContents(True)
        self.background_label.setGeometry(0, 0, self.width(), self.height())

        # Campo de texto
        self.text_input = QLineEdit(self)
        self.text_input.setPlaceholderText("Digite o ID da Tela")
        self.text_input.setGeometry(300, 250, 200, 40)

        # Botão
        self.button = QPushButton("Salvar", self)
        self.button.setGeometry(350, 300, 100, 40)
        self.button.clicked.connect(self.salvar_config)

        # Mensagem
        self.status_label = QLabel("", self)
        self.status_label.setGeometry(250, 350, 300, 40)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 18px; color: white;")

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(250, 400, 300, 25)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
                color: black;
            }
            QProgressBar::chunk {
                background-color: #00cc66;
                width: 10px;
            }
        """)

        # Ordem visual
        self.text_input.raise_()
        self.button.raise_()
        self.status_label.raise_()

        self.resizeEvent = self.on_resize

    def salvar_config(self):
        entrada = self.text_input.text().strip()
        if entrada:
            partes = entrada.split("_")
            cliente_id = partes[0]
            modelo_tela = int(partes[1]) if len(partes) > 1 and partes[1].isdigit() else 0

            config = {
                "tela_id": cliente_id,
                "modelo": modelo_tela
            }

            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f)

            self.status_label.setText("📡 Fazendo download dos arquivos...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.button.setEnabled(False)
            self.text_input.setEnabled(False)

            # Iniciar atualizações em thread separada
            def atualizar():
                executar_atualizacoes(callback_progresso=self.progress_bar.setValue)
                # Finalizar na thread principal do Qt
                QTimer.singleShot(0, self.finalizar_config)

            Thread(target=atualizar, daemon=True).start()

    def finalizar_config(self):
        self.progress_bar.setValue(100)
        self.status_label.setText("✅ Arquivos baixados e extraídos!")
        self.close()

    def on_resize(self, event):
        pixmap = QPixmap("assets/background.png")
        pixmap = pixmap.scaled(self.width(), self.height(), Qt.AspectRatioMode.KeepAspectRatioByExpanding)
        self.background_label.setPixmap(pixmap)
        self.background_label.setGeometry(0, 0, self.width(), self.height())

# 🔹 Execução isolada
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConfigIni()
    window.show()
    sys.exit(app.exec())
