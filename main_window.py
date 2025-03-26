from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QSizePolicy, QSpacerItem
from PyQt6.QtCore import Qt  # 🔹 Import necessário para o modo fullscreen
from componentes.header import Header
from componentes.videos import VideoWidget
from componentes.news import NewsWidget
from componentes.footer import Footer
from componentes.info_condo import InfoWidget
from componentes.live import LiveWidget
from componentes.time import TimerWidget
from componentes.services import ServicesWidget


class ElevatorScreen(QMainWindow):
    def __init__(self):
        super().__init__()

        # 📌 Configuração da Janela
        self.setWindowTitle("Tela do Elevador")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)  # 🔹 Remove bordas
        self.showFullScreen()  # 🔹 Inicia em tela cheia

        # 📌 Definir a imagem de fundo
        self.setStyleSheet("""
            QMainWindow {
                background-image: url('assets/background.png');
                background-position: center;
                background-repeat: no-repeat;
                background-size: cover;
            }
        """)

        # 📌 Criar o widget principal e os layouts
        spacer = QSpacerItem(
            15, 15, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        spacer2 = QSpacerItem(
            10, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        main_widget = QWidget()
        mainV_layout = QVBoxLayout()
        mainH_layout = QHBoxLayout()

        # 📌 Criar Widgets para as colunas
        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)

        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)

        # 📌 Adicionar componentes ao layout vertical principal
        header = Header()
        mainV_layout.addWidget(header, 1)

        video_widget = VideoWidget()
        mainV_layout.addWidget(video_widget, 4)

        # 📌 Criar as colunas
        mainV_layout.addItem(spacer2)
        mainH_layout.addWidget(left_column, 2)
        mainH_layout.addWidget(right_column, 2)

        # 📌 Adicionar widgets à coluna da esquerda
        services_widget = ServicesWidget()
        left_layout.addWidget(services_widget, 1)
        info_widget = InfoWidget()
        left_layout.addWidget(info_widget, 2)

        # 📌 Adicionar widgets à coluna da direita
        news_widget = NewsWidget()
        right_layout.addWidget(news_widget, 4)

        right_layout.addItem(spacer)

        live_widget = LiveWidget()
        right_layout.addWidget(live_widget, 3)

        timer_widget = TimerWidget()
        right_layout.addWidget(timer_widget, 1)

        # 📌 Adicionar o layout das colunas no layout principal
        mainV_layout.addLayout(mainH_layout, 6)

        # 📌 Adicionar o rodapé ao final
        footer = Footer()
        mainV_layout.addWidget(footer, 1)

        # 📌 Configurar o layout principal e a central widget
        main_widget.setLayout(mainV_layout)
        self.setCentralWidget(main_widget)
