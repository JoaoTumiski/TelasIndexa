from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QTimer, QDateTime, QLocale

# 📌 Definir o idioma padrão para Português do Brasil
QLocale.setDefault(QLocale(QLocale.Language.Portuguese, QLocale.Country.Brazil))


class TimerWidget(QWidget):
    def __init__(self):
        super().__init__()

        # 📌 Layout Vertical para separar Data e Hora
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)  # Pequeno espaçamento entre data e hora

        # 📌 Label para a Data
        self.date_label = QLabel()
        self.date_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_label.setStyleSheet("color: white;")

        # 📌 Label para a Hora (Fonte maior)
        self.time_label = QLabel()
        self.time_label.setFont(QFont("Arial", 36, QFont.Weight.Bold))  # Hora maior
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("color: white;")

        # 📌 Adicionar Labels ao Layout
        layout.addWidget(self.date_label)
        layout.addWidget(self.time_label)
        self.setLayout(layout)

        # 📌 Atualizar a hora em tempo real
        self.update_time()  # Inicializa com a hora correta
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # Atualiza a cada 1 segundo

    def update_time(self):
        """ Atualiza a Data e Hora em tempo real com idioma PT-BR. """
        current_datetime = QDateTime.currentDateTime()  # Obtém a hora do sistema (NUC)

        # 📌 Criar um objeto QLocale para garantir PT-BR
        locale = QLocale(QLocale.Language.Portuguese, QLocale.Country.Brazil)

        formatted_date = locale.toString(current_datetime, "dddd dd/MM/yyyy")  # Exemplo: "segunda-feira, 11/03/2025"
        formatted_time = current_datetime.toString("HH:mm")  # Exemplo: "14:35:20"

        # Deixar a primeira letra maiúscula
        formatted_date = formatted_date.capitalize()

        self.date_label.setText(formatted_date)
        self.time_label.setText(formatted_time)
