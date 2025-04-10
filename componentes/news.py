import os
import json
import qrcode
from PIL import Image
import requests
from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath
from config.database import supabase
from atualizadores import noticias_update


# 🔥 Caminhos dos arquivos locais
NEWS_JSON_PATH = "cache/noticias.json"
QR_CODE_FOLDER = "cache/qrcodes"
S3_BUCKET = "imagens-noticias"
S3_PREFIX = "News/"
LOCAL_NEWS_FOLDER = os.path.join("cache", "News")
CONFIG_PATH = "config.json"

# 🔥 Criar pastas caso não existam
os.makedirs("cache", exist_ok=True)
os.makedirs(QR_CODE_FOLDER, exist_ok=True)

def arredondar_pixmap(pixmap, radius):
        """Retorna um QPixmap com cantos arredondados."""
        if pixmap.isNull():
            return pixmap

        size = pixmap.size()
        rounded = QPixmap(size)
        rounded.fill(Qt.GlobalColor.transparent)

        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, size.width(), size.height(), radius, radius)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()

        return rounded

class NewsWidget(QWidget):
    def __init__(self):
        super().__init__()

        # 🔄 Força a verificação no Supabase na inicialização
        noticias_update.verificar_e_atualizar_noticias()

        # 🔥 Criar QR Code folder dentro do objeto
        self.qr_folder = QR_CODE_FOLDER
        # 📌 Limpar cache de QR Codes ao iniciar
        self.clear_qr_cache()

        # 📌 Criar a pasta para os QR Codes se não existir
        os.makedirs(self.qr_folder, exist_ok=True)

        # 📌 Layout principal (background)
        main_layout = QVBoxLayout()

        # 📌 Criar um QWidget para servir de contêiner do fundo (para garantir bordas arredondadas)
        self.background_container = QWidget(self)
        self.background_container.setObjectName("backgroundContainer")  # 🔹 Para estilização no QSS

        # 📌 Criar um QLabel para exibir a imagem de fundo dentro do container
        self.background_label = QLabel(self.background_container)
        self.background_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.background_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.background_label.setStyleSheet("border-radius: 20px;")

        # 📌 Definir estilos para garantir bordas arredondadas e fundo ajustado
        self.background_container.setStyleSheet("""
            QWidget#backgroundContainer {
                border-radius: 20px;
                background-color: #171615; /* Cor de fallback */
            }
        """)

        # 📌 Enviar para o fundo e garantir que ocupe toda a tela
        self.background_container.lower()

        # 📌 Criar um overlay escuro e transparente sobre a imagem de fundo
        self.overlay = QWidget(self.background_container)
        self.overlay.setObjectName("overlay")

        # 📌 Estilizar o overlay para ficar escuro e transparente
        self.overlay.setStyleSheet("""
            QWidget#overlay {
                background-color: rgba(0, 0, 0, 200 ); /* 🔹 Cor preta com 150/255 de opacidade */
                border-radius: 20px; /* 🔹 Mantém bordas arredondadas */
            }
        """)

        # 🔹 Coloca o overlay acima da imagem de fundo
        self.overlay.raise_()

        # 📌 Layout superior (QR Code e Título)
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)

        # 📌 Quadrado arredondado à esquerda (QR Code da Notícia)
        self.qr_label = QLabel()
        self.qr_label.setFixedSize(125, 125)
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_label.setScaledContents(True)
        self.qr_label.setStyleSheet("""
            background-color: #fff;
            border-radius: 20px;
            padding: 5px;
        """)

        # 📌 Título à direita
        self.title_label = QLabel("Título")
        self.title_label.setWordWrap(True)  # 🔥 Permite quebra de linha
        self.title_label.setStyleSheet("color: #2fc6cf; font-size: 28px; font-weight: bold;")
        self.title_label.setContentsMargins(0, 0, 10, 0)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        # 📌 Adicionar itens ao layout superior
        top_layout.addWidget(self.qr_label)
        top_layout.addStretch()
        top_layout.addWidget(self.title_label)

        # 📌 Layout central (Notícia e Logo)
        center_layout = QVBoxLayout()
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(10)

        # 📌 Notícia (Texto da notícia)
        self.news_label = QLabel("Notícia")
        self.news_label.setStyleSheet("color: #fff; font-size: 32px; font-weight: bold;")
        self.news_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.news_label.setWordWrap(True)

        # 📌 Criar Layout Horizontal para Centralizar o Logo
        logo_layout = QHBoxLayout()
        logo_layout.setContentsMargins(0, 0, 0, 0)  # Remove margens
        logo_layout.setSpacing(0)

        # 📌 Logo da fonte de notícia
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setFixedSize(180, 50)  # 🔹 Tamanho fixo para o logo
        self.logo_label.setScaledContents(True)

        # 📌 Adicionar a logo ao layout e centralizar
        logo_layout.addStretch()
        logo_layout.addWidget(self.logo_label)
        logo_layout.addStretch()

        # 📌 Adicionar itens ao layout central
        center_layout.addStretch()
        center_layout.addWidget(self.news_label)
        center_layout.addStretch()
        center_layout.addLayout(logo_layout)

        # 📌 Adicionar layouts ao layout principal
        # 📌 Definir o QLabel de fundo como um background fixo
        self.background_label.lower()  # 🔹 Envia o QLabel para o fundo, atrás dos outros widgets
        self.background_label.setGeometry(0, 0, self.width(), self.height())  # 🔹 Ocupa toda a área do widget
        main_layout.addLayout(top_layout)
        main_layout.addLayout(center_layout)
        self.setLayout(main_layout)

        # 📌 Criar JSON inicial caso não exista
        if not os.path.exists(NEWS_JSON_PATH):
            noticias_update.salvar_noticias_localmente({"portal_cidade": [], "jovempan": []}, "2000-01-01T00:00:00")

        # 📌 Carregar as notícias do JSON
        self.news_list = self.get_news_from_json()
        self.current_news_index = 0

        # 📌 Se houver notícias, exibir a primeira
        if self.news_list:
            self.update_news()

            # 📌 Criar Timer para alternar notícias a cada 15 segundos
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.next_news)
            self.timer.start(15000)
        else:
            self.news_label.setText("⚠️ Nenhuma notícia disponível!")

        # 🔥 Criar um timer para verificar atualizações a cada 20 minutos
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.atualizar_noticias)
        self.update_timer.start(1200000)  # 20 minutos (1.200.000 ms)

    def get_news_from_json(self):
        """Obtém as notícias do JSON salvo localmente e gera QR Codes intercalados em loop entre J e P."""
        noticias, _ = noticias_update.carregar_noticias_local()
        if not noticias:
            return []

        lista_jp = []
        lista_pc = []

        for origem, lista in noticias.items():
            for noticia in lista:
                titulo = noticia.get("titulo", "Sem título") 
                link = noticia.get("link", "")
                categoria = noticia.get("categoria", "Geral")
                imagem = noticia.get("imagem")
                qr_path = self.generate_qr_code(link)

                item = {
                    "titulo": titulo,
                    "categoria": categoria,
                    "qr_code": qr_path if os.path.exists(qr_path) else None,
                    "origem": origem,
                    "imagem": imagem
                }

                if origem == "jovempan":
                    lista_jp.append(item)
                elif origem == "portal_cidade":
                    lista_pc.append(item)

        if not lista_jp and not lista_pc:
            return []

        intercalados = []
        i_jp = 0
        i_pc = 0

        # 🔁 Gera uma lista intercalada até o maior número de combinações possível
        total = max(len(lista_jp), len(lista_pc)) * 2  # dobra pois intercalamos os dois
        for _ in range(total):
            if lista_jp:
                intercalados.append(lista_jp[i_jp % len(lista_jp)])
                i_jp += 1
            if lista_pc:
                intercalados.append(lista_pc[i_pc % len(lista_pc)])
                i_pc += 1

        return intercalados


    def update_news(self):
        """Atualiza a notícia exibida no widget"""
        if self.news_list:
            noticia = self.news_list[self.current_news_index]

            # 🔹 Obter título e categoria corretamente
            titulo = noticia.get("titulo", "Título não encontrado")
            categoria = noticia.get("categoria", "Sem categoria")

            # 🔹 Atualizar o título da categoria no topo
            self.title_label.setText(categoria)  # ⬅️ Agora exibe a categoria no topo

            # 🔹 Atualizar a logo com base na origem
            origem = noticia.get("origem", "")
            logo_path = f"assets/logotipos/{origem}.png"
            if os.path.exists(logo_path):
                pixmap_logo = QPixmap(logo_path)
                self.logo_label.setPixmap(pixmap_logo)
                self.logo_label.show()
            else:
                self.logo_label.clear()

            # 🔹 Atualizar o texto da notícia no centro do card
            self.news_label.setText(titulo)  # ⬅️ Agora exibe apenas o título no centro

            # 📌 Atualizar QR Code
            if noticia.get("qr_code") and os.path.exists(noticia["qr_code"]):
                pixmap = QPixmap(noticia["qr_code"])
                if not pixmap.isNull():
                    self.qr_label.setPixmap(pixmap)
                    self.qr_label.show()
                else:
                    print(f"⚠️ Erro ao carregar QR Code: {noticia['qr_code']}")
                    self.qr_label.hide()
            else:
                self.qr_label.hide()

            # 🔹 Atualizar imagem de fundo se for do portal_cidade e tiver imagem
            imagem_nome = noticia.get("imagem")
            if noticia.get("origem") == "portal_cidade" and imagem_nome:
                imagem_path = os.path.join("cache", "News", imagem_nome)
                if os.path.exists(imagem_path):
                    pixmap_bg = QPixmap(imagem_path)
                    if not pixmap_bg.isNull():
                        rounded_pixmap = arredondar_pixmap(pixmap_bg, 30)
                        self.background_label.setPixmap(rounded_pixmap)
                        self.background_label.setScaledContents(True)
                    else:
                        self.background_label.clear()
                else:
                    self.background_label.clear()
            else:
                self.background_label.clear()

            self.update()

    def next_news(self):
        """Alterna para a próxima notícia no loop"""
        self.current_news_index = (self.current_news_index + 1) % len(self.news_list)
        self.update_news()

    def atualizar_noticias(self):
        """Atualiza as notícias verificando o Supabase e atualiza o label."""
        print("🔄 Atualizando notícias no Widget...")
        novas_noticias = noticias_update.verificar_e_atualizar_noticias()
        if novas_noticias:
            self.clear_qr_cache()  # 🔥 Limpa os QR Codes antigos
            self.news_list = self.get_news_from_json()
            self.update_news()

    def clear_qr_cache(self):
        """Limpa QR Codes antigos ao iniciar, mantendo apenas os do JSON salvo localmente."""
        if not os.path.exists(NEWS_JSON_PATH):
            print("⚠️ Nenhum JSON encontrado, pulando limpeza de QR Codes.")
            return  # Se o JSON não existe, não há como validar

        try:
            with open(NEWS_JSON_PATH, "r", encoding="utf-8") as file:
                data = json.load(file)
                noticias = data.get("noticias", {})

                # 🔹 Obtém todos os links do JSON para gerar IDs de QR Codes válidos
                valid_qr_codes = set()
                for fonte in noticias.values():  # Itera por 'portal_cidade' e 'jovempan'
                    for noticia in fonte:
                        if "link" in noticia:
                            valid_qr_codes.add(f"{hash(noticia['link'])}.png")

                # 🔹 Remove QR Codes que não estão mais no JSON
                for filename in os.listdir(self.qr_folder):
                    if filename.endswith(".png") and filename not in valid_qr_codes:
                        file_path = os.path.join(self.qr_folder, filename)
                        os.remove(file_path)
                        print(f"🗑️ Removido QR Code antigo: {file_path}")

        except Exception as e:
            print(f"❌ Erro ao limpar QR Codes antigos: {e}")


    def generate_qr_code(self, link):
        """Gera um QR Code para o link da notícia via endpoint do backend"""
        if not link:
            return None

        # ⚠️ Substitua pelo domínio público ou IP do seu servidor
        backend_url = f"http://15.228.8.3:8000/leitura?cliente_id={noticias_update.CLIENTE_ID}&link={link}"
        qr_filename = f"{hash(backend_url)}.png"
        qr_path = os.path.join(self.qr_folder, qr_filename)

        if not os.path.exists(qr_path):
            qr = qrcode.make(backend_url)
            qr.save(qr_path)

        return qr_path
    
    def resizeEvent(self, event):
        """Redimensiona o fundo e o overlay para cobrir toda a área"""
        self.background_container.setGeometry(0, 0, self.width(), self.height())  # Fundo
        self.background_label.setGeometry(0, 0, self.width(), self.height())  # Imagem
        self.overlay.setGeometry(0, 0, self.width(), self.height())  # Overlay escuro
        super().resizeEvent(event)
