import os
import json
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget, QSizePolicy
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath
from PyQt6.QtCore import Qt, QTimer, QRectF


class ServicesWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        # 🔹 Última versão conhecida do JSON (para comparação)
        self.last_json_state = None 

        # 📌 Layout para centralizar a imagem
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 📌 Criar QLabel para exibir as imagens
        self.Services = QLabel()
        self.Services.setScaledContents(False)
        self.Services.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.Services.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.Services.setStyleSheet("background: transparent;")


        # 📌 Definir tamanho fixo do widget (altura) e expansível na largura
        self.setFixedHeight(200)
        self.Services.setFixedWidth(540)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # 📌 Remover o fundo para exibir apenas a imagem
        self.setStyleSheet("padding: 0px; margin: 0px;")  # Sem background

        layout.addWidget(self.Services)
        self.setLayout(layout)

        # 📌 Caminho dos arquivos extraídos do ZIP
        self.json_path = "cache/update.json"
        self.image_folder = "cache/Banners"

        # 📌 Carregar a lista de banners do JSON
        self.image_list = self.get_images_from_json()
        self.current_image_index = 0

         # 📌 Criar Timer para monitorar mudanças no JSON a cada 30 segundos
        self.json_check_timer = QTimer(self)
        self.json_check_timer.timeout.connect(self.check_for_json_update)
        self.json_check_timer.start(30000)  # 🔹 Verifica a cada 30s

        # 📌 Se houver imagens, exibir a primeira
        if self.image_list:
            self.update_image()

            # 📌 Criar Timer para alternar imagens a cada 10 segundos
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.next_image)
            self.timer.start(10000)  # 10 segundos (10000ms)
        else:
            self.Services.setText("⚠️ Nenhum banner encontrado!")

    def check_for_json_update(self):
        """Verifica se houve mudança no JSON e recarrega os banners se necessário."""
        if not os.path.exists(self.json_path):
            return

        try:
            with open(self.json_path, "r", encoding="utf-8") as file:
                new_json_state = file.read()  # Lê o JSON como string para comparação

            if new_json_state != self.last_json_state:  # Se mudou, recarrega os banners
                print("🔄 Detecção de mudança no JSON! Atualizando banners...")

                self.last_json_state = new_json_state  # Atualiza o estado conhecido
                self.image_list = self.get_images_from_json()  # Recarrega a lista de imagens
                self.current_image_index = 0  # Reinicia a exibição
                self.update_image()  # Atualiza o banner exibido

        except Exception as e:
            print(f"❌ Erro ao verificar mudanças no JSON: {e}")

    def get_images_from_json(self):
        """Obtém os banners válidos listados no JSON extraído, ignorando deletados."""
        if not os.path.exists(self.json_path):
            print(f"⚠️ Arquivo JSON não encontrado: {self.json_path}")
            return []

        try:
            with open(self.json_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                banners = data.get("Banners", [])

                image_paths = []
                for banner in banners:
                    # 🔹 Ignora banners com status "deleted"
                    if banner.get("status") == "deleted":
                        continue  

                    image_name = os.path.basename(banner["imagem"])  # Pega apenas o nome do arquivo
                    image_path = os.path.join(self.image_folder, image_name)

                    if os.path.exists(image_path):  # Confirma que o arquivo existe
                        image_paths.append(image_path)
                    else:
                        print(f"⚠️ Arquivo de banner não encontrado: {image_path}")

                return image_paths

        except Exception as e:
            print(f"❌ Erro ao processar JSON: {e}")
            return []


    def update_image(self):
        """Atualiza a imagem exibida no QLabel com bordas arredondadas"""
        if self.image_list:
            image_path = self.image_list[self.current_image_index]
            pixmap = QPixmap(image_path)

            # Redimensiona mantendo proporção
            scaled = pixmap.scaled(
                self.Services.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            # Cria QPixmap transparente para aplicar máscara
            rounded = QPixmap(scaled.size())
            rounded.fill(Qt.GlobalColor.transparent)

            # Desenha a imagem com cantos arredondados
            painter = QPainter(rounded)
            try:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                path = QPainterPath()
                path.addRoundedRect(QRectF(rounded.rect()), 20, 20)
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, scaled)
            finally:
                painter.end()

            self.Services.setPixmap(rounded)

    def next_image(self):
        """Alterna para a próxima imagem no loop"""
        self.current_image_index = (self.current_image_index + 1) % len(self.image_list)
        self.update_image()

    def resizeEvent(self, event):
        """Reajusta a imagem quando a janela for redimensionada"""
        self.update_image()
        super().resizeEvent(event)
