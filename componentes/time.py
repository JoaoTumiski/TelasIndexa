import sys
import os
import json
import urllib.request
import requests
import traceback
import datetime

from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QDateTime, QLocale
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QStackedLayout, QGraphicsOpacityEffect
)

QLocale.setDefault(QLocale(QLocale.Language.Portuguese, QLocale.Country.Brazil))

CONDICOES_PT = {
    1000: "Ensolarado", 1003: "Parcialmente nublado", 1006: "Nublado", 1009: "Encoberto", 1030: "Névoa",
    1063: "Chuva isolada", 1066: "Neve isolada", 1069: "Chuva congelante isolada", 1072: "Garoa congelante isolada",
    1087: "Possibilidade de trovoadas", 1114: "Neve com vento", 1117: "Nevasca", 1135: "Nevoeiro",
    1147: "Nevoeiro congelante", 1150: "Garoa leve isolada", 1153: "Garoa leve", 1168: "Garoa congelante",
    1171: "Garoa congelante forte", 1180: "Chuva leve isolada", 1183: "Chuva leve", 1186: "Chuva moderada ocasional",
    1189: "Chuva moderada", 1192: "Chuva forte ocasional", 1195: "Chuva forte", 1198: "Chuva congelante leve",
    1201: "Chuva congelante moderada/forte", 1204: "Granizo leve", 1207: "Granizo moderado/forte",
    1210: "Neve leve isolada", 1213: "Neve leve", 1216: "Neve moderada isolada", 1219: "Neve moderada",
    1222: "Neve forte isolada", 1225: "Neve forte", 1237: "Granizo", 1240: "Pancada de chuva leve",
    1243: "Pancada de chuva moderada/forte", 1246: "Pancada de chuva torrencial", 1249: "Pancadas de granizo leve",
    1252: "Pancadas de granizo moderado/forte", 1255: "Pancadas de neve leve", 1258: "Pancadas de neve moderada/forte",
    1261: "Pancadas leves de granizo", 1264: "Pancadas fortes de granizo", 1273: "Chuva com trovoada leve",
    1276: "Chuva com trovoada moderada/forte", 1279: "Neve com trovoada leve", 1282: "Neve com trovoada moderada/forte"
}


class FlipClockClimaWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(420, 180)

        self.stack = QStackedLayout()
        self.stack.addWidget(self.criar_layout_relogio())
        self.stack.addWidget(self.criar_layout_clima())

        # 👉 Envolver o stack em um widget de container
        stack_widget = QWidget()
        stack_widget.setLayout(self.stack)

        # 👉 Criar um layout centralizador
        centralizador = QVBoxLayout()
        centralizador.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Isso é o segredo
        centralizador.addWidget(stack_widget)

        self.setLayout(centralizador)

        self.current_index = 0
        self.hora_timer = QTimer(self, timeout=self.atualizar_relogio)
        self.hora_timer.start(1000)

        self.troca_timer = QTimer(self, timeout=self.trocar_tela)
        self.troca_timer.start(5000)

        self.atualizar_relogio()
        self.atualizar_clima()

        self.timer_clima = QTimer(self)
        self.timer_clima.timeout.connect(self.atualizar_clima)
        self.timer_clima.start(20 * 60 * 1000)

    def criar_layout_relogio(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label_data = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        self.label_data.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self.label_data.setStyleSheet("color: white;")

        self.label_hora = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        self.label_hora.setFont(QFont("Arial", 36, QFont.Weight.Bold))
        self.label_hora.setStyleSheet("color: white;")

        layout.addWidget(self.label_data)
        layout.addWidget(self.label_hora)

        return widget
    
    def atualizar_clima(self):
        url = "http://15.228.8.3:8000/api/clima"  # substitua pelo IP se necessário
        try:
            print("🔄 Buscando clima da API...")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            dados = response.json()

            with open("cache/clima_cache.json", "w", encoding="utf-8") as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)

            print("✅ Clima atualizado com sucesso.")
        except Exception as e:
            print("⚠️ Erro ao buscar clima da API:", e)
            traceback.print_exc()
            print("🟡 Usando previsão local com base na hora atual.")

    def obter_forecast_mais_proximo(self, dados):
        agora = datetime.datetime.now()
        melhor_forecast = dados["forecast"]["forecastday"][0]
        for dia in dados["forecast"]["forecastday"]:
            data = datetime.datetime.strptime(dia["date"], "%Y-%m-%d")
            if data.date() == agora.date():
                return dia
        return melhor_forecast


    def criar_layout_clima(self):
        widget = QWidget()
        layout_principal = QHBoxLayout(widget)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(10)

        if not os.path.exists("cache/clima_cache.json"):
            layout_principal.addWidget(QLabel("⛅ Sem dados de clima"))
            return widget

        try:
            with open("cache/clima_cache.json", "r", encoding="utf-8") as f:
                dados = json.load(f)

            clima_hoje = dados["current"]
            previsoes = [self.obter_forecast_mais_proximo(dados)] + dados["forecast"]["forecastday"][1:]
            layout_principal.addLayout(self.criar_bloco_hoje(clima_hoje, previsoes[0]), stretch=2)
            layout_principal.addLayout(self.criar_blocos_previsao(previsoes[1:3]), stretch=1)

        except Exception as e:
            aviso = QLabel("Erro ao carregar clima")
            aviso.setStyleSheet("font-size: 16px; color: red;")
            layout_principal.addWidget(aviso)
            print(f"[ERRO] Falha ao processar JSON de clima: {e}")

        return widget

    def criar_bloco_hoje(self, clima, previsao):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = self.carregar_icone(clima["condition"]["icon"], 80)
        layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)

        temp = clima["temp_c"]
        code = clima["condition"]["code"]
        texto = CONDICOES_PT.get(code, clima["condition"]["text"])
        chance = previsao["day"]["daily_chance_of_rain"]

        temp_label = QLabel(f"{temp:.1f}°C", alignment=Qt.AlignmentFlag.AlignCenter)
        temp_label.setStyleSheet("font-size: 28px; font-weight: bold; color: white;")

        desc_label = QLabel(f"{texto}\n{chance}% Chuva", alignment=Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")

        layout.addWidget(temp_label)
        layout.addWidget(desc_label)
        return layout

    def criar_blocos_previsao(self, dias):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        for dia in dias:
            sub_layout = QVBoxLayout()
            sub_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            icon = self.carregar_icone(dia["day"]["condition"]["icon"], 48)
            sub_layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)
            min_temp = dia["day"]["mintemp_c"]
            max_temp = dia["day"]["maxtemp_c"]
            texto = CONDICOES_PT.get(dia["day"]["condition"]["code"], dia["day"]["condition"]["text"])

            info = QLabel(f"{min_temp:.1f}°C - {max_temp:.1f}°C\n{texto}", alignment=Qt.AlignmentFlag.AlignCenter)
            info.setStyleSheet("font-size: 12px; font-weight: bold; color: white;")
            sub_layout.addWidget(info)
            layout.addLayout(sub_layout)

        return layout

    def carregar_icone(self, url, size):
        pixmap = QPixmap()
        try:
            img_data = urllib.request.urlopen("https:" + url).read()
            pixmap.loadFromData(img_data)
        except:
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)

        label = QLabel()
        label.setPixmap(pixmap)
        label.setFixedSize(size, size)
        label.setScaledContents(True)
        return label

    def atualizar_relogio(self):
        agora = QDateTime.currentDateTime()
        locale = QLocale(QLocale.Language.Portuguese, QLocale.Country.Brazil)
        self.label_data.setText(locale.toString(agora, "dddd dd/MM/yyyy").capitalize())
        self.label_hora.setText(agora.toString("HH:mm"))

    def trocar_tela(self):
        atual = self.stack.currentWidget()
        efeito = QGraphicsOpacityEffect(atual)
        atual.setGraphicsEffect(efeito)

        anim = QPropertyAnimation(efeito, b"opacity", self)
        anim.setDuration(400)
        anim.setStartValue(1)
        anim.setEndValue(0)
        anim.finished.connect(self.finalizar_troca)
        anim.start()
        self.animacao = anim

    def finalizar_troca(self):
        self.current_index = (self.current_index + 1) % 2
        if self.current_index == 1:
            self.stack.removeWidget(self.stack.widget(1))
            self.stack.insertWidget(1, self.criar_layout_clima())
        self.stack.setCurrentIndex(self.current_index)

        proximo = self.stack.currentWidget()
        efeito = QGraphicsOpacityEffect(proximo)
        proximo.setGraphicsEffect(efeito)

        anim = QPropertyAnimation(efeito, b"opacity", self)
        anim.setDuration(400)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.start()
        self.animacao = anim


if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = FlipClockClimaWidget()
    janela.show()
    sys.exit(app.exec())
