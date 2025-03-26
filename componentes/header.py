from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtCore import Qt
import os
import json
import re  # 📌 Para manipular strings e separar palavras

class Header(QLabel):
    def __init__(self):
        super().__init__()

        # 📌 Caminho do JSON extraído do ZIP
        self.json_path = "cache/update.json"

        # 📌 Obter o nome da tela do JSON e formatá-lo corretamente
        self.screen_name = self.get_screen_name()

        # 📌 Caminho da fonte personalizada
        font_path = "assets/fonts/BebasNeue.ttf"

        # 📌 Verifica se o arquivo da fonte existe
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            font_families = QFontDatabase.applicationFontFamilies(font_id)

            if font_families:
                self.setFont(QFont(font_families[0], 48, QFont.Weight.Bold))  # Aplica a fonte personalizada
            else:
                self.setFont(QFont("Arial", 34, QFont.Weight.Bold))  # Fallback para Arial
        else:
            print(f"⚠️ Fonte não encontrada: {font_path}. Usando Arial.")
            self.setFont(QFont("Arial", 34, QFont.Weight.Bold))  # Fallback para Arial

        # 📌 Definir o nome da tela
        self.setText(self.screen_name)

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            color: white;
            padding: 0px;
            margin: 0px;
            border: none;
        """)

    def get_screen_name(self):
        """Obtém e formata corretamente o nome da tela a partir do JSON"""
        if not os.path.exists(self.json_path):
            print(f"⚠️ Arquivo JSON não encontrado: {self.json_path}")
            return "Indexa"  # Nome padrão se o JSON não existir

        try:
            with open(self.json_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                screen_name = data.get("ScreenName", "")

                # 📌 Se não houver nome, retornar "Indexa"
                if not screen_name:
                    return "Indexa"

                # 📌 Formatar corretamente o nome para separar palavras maiúsculas
                screen_name = self.formatar_nome(screen_name)

                return screen_name

        except Exception as e:
            print(f"❌ Erro ao carregar o JSON: {e}")
            return "Indexa"  # Fallback se houver erro

    def formatar_nome(self, nome):
        """Separa palavras maiúsculas para tornar o nome mais legível"""
        nome_formatado = re.sub(r'([a-z])([A-Z])', r'\1 \2', nome)  # Adiciona espaço antes de letras maiúsculas
        return nome_formatado.strip()

