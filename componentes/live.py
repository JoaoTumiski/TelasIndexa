import os
import json
import sys
import socket
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal, QUrl, QSizeF, QRectF
from PyQt6.QtGui import QPainterPath, QRegion,QTransform
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, QSizePolicy
from PyQt6.QtMultimediaWidgets import QGraphicsVideoItem
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from config.database import supabase

LIVE_JSON_PATH = "cache/live.json"
CONFIG_PATH = "config.json"

class LiveReconnectThread(QThread):
    finished = pyqtSignal()

    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def run(self):
        self.widget.set_media()
        self.widget.start_live()
        self.finished.emit()

class LiveVerifierThread(QThread):
    resultado = pyqtSignal(bool)

    def __init__(self, player):
        super().__init__()
        self.player = player
        self.ultimo_tempo = -1

    def run(self):
        self.msleep(500)
        tempo_atual = self.player.position()
        if self.player.mediaStatus() != QMediaPlayer.MediaStatus.BufferedMedia or tempo_atual == self.ultimo_tempo:
            self.resultado.emit(False)
        else:
            self.resultado.emit(True)
            self.ultimo_tempo = tempo_atual

class RoundedGraphicsView(QGraphicsView):
    def __init__(self, scene, video_item, *args, **kwargs):
        super().__init__(scene, *args, **kwargs)
        self.video_item = video_item

    def resizeEvent(self, event):
        super().resizeEvent(event)
        size = self.viewport().size()
        self.video_item.setSize(QSizeF(size))
        self.scene().setSceneRect(0, 0, size.width(), size.height())
        self.set_rounded_corners(radius=20)

    def set_rounded_corners(self, radius=20):
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), radius, radius)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)


def carregar_config():
    if not os.path.exists(CONFIG_PATH):
        return None
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            config_data = json.load(file)
            return int(config_data.get("tela_id", 102))
    except:
        return 0

CLIENTE_ID = carregar_config()

from config.database import supabase

def verificar_e_atualizar_live():
    url_local, timestamp_local = carregar_live_local()

    if not supabase:
        print("⚠️ Supabase indisponível. Usando cache local.")
        return url_local

    try:
        response = supabase.table("cameras").select("url, data_criacao") \
            .eq("cliente_id", CLIENTE_ID).order("data_criacao", desc=True).execute()

        if response.data:
            url_supabase = response.data[0]["url"]
            timestamp_supabase = response.data[0]["data_criacao"]
            if timestamp_supabase != timestamp_local:
                salvar_live_localmente(url_supabase, timestamp_supabase)
                return url_supabase

    except Exception as e:
        print(f"⚠️ Erro ao buscar live no Supabase: {e}")

    return url_local

def salvar_live_localmente(url, data_criacao):
    try:
        with open(LIVE_JSON_PATH, "w", encoding="utf-8") as file:
            json.dump({"url": url, "data_criacao": data_criacao}, file, indent=4, ensure_ascii=False)
    except:
        pass

def carregar_live_local():
    if not os.path.exists(LIVE_JSON_PATH):
        return None, None
    try:
        with open(LIVE_JSON_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data.get("url"), data.get("data_criacao")
    except:
        return None, None

class LiveWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.verificacoes_paradas = 0
        self.internet_conectada = True
        self.reconectando = False

        self.lives = [verificar_e_atualizar_live()]
        self.live_url = self.lives[0] if self.lives else None
        self.current_live_index = 0

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Cria a cena e item de vídeo
        self.scene = QGraphicsScene()
        self.video_item = QGraphicsVideoItem()
        self.scene.addItem(self.video_item)

        self.zoom_factor = 1.4
        transform = QTransform()
        transform.scale(self.zoom_factor, self.zoom_factor)
        self.video_item.setTransform(transform)

        # opcional: centraliza melhor o vídeo dentro do widget
        size = self.size()
        self.video_item.setPos(
            -(size.width() * (self.zoom_factor - 1)) / 2,
            -(size.height() * (self.zoom_factor - 1)) / 2 + 30
        )

        # Usa a RoundedGraphicsView com cantos arredondados reais
        self.view = RoundedGraphicsView(self.scene, self.video_item)
        self.view.setStyleSheet("border: none; background-color: black;")
        self.view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.view.setSizePolicy(self.sizePolicy())  # garante que ocupe o espaço do widget
        self.layout.addWidget(self.view)

        # Configura player
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(0.0)
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_item)

        self.set_media()

        # Destroi o player atual
        self.player.stop()
        self.player.deleteLater()

        # Cria um novo player do zero
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(0.0)
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_item)

        # Reconfigura a mídia e inicia
        self.set_media()
        QTimer.singleShot(500, self.start_live)

        # Timers
        self.switch_timer = QTimer(self)
        self.switch_timer.timeout.connect(self.switch_live)
        self.switch_timer.start(30000)

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.atualizar_live)
        self.update_timer.start(1200000)

        self.verificador_timer = QTimer(self)
        self.verificador_timer.timeout.connect(self.verificar_live)
        self.verificador_timer.start(10000)

        self.internet_timer = QTimer(self)
        self.internet_timer.timeout.connect(self.verificar_conexao_internet)
        self.internet_timer.start(5000)

        

    def set_media(self, url=None):
        if not url:
            url = self.live_url
        if isinstance(url, list):
            url = url[0]
        if url:
            self.live_url = url
            self.player.setSource(QUrl(self.live_url))
            print(f"🎬 Mídia configurada: {self.live_url}")

    def start_live(self):
        if self.live_url:
            self.player.play()

    def switch_live(self):
        if len(self.lives) > 1:
            self.current_live_index = (self.current_live_index + 1) % len(self.lives)
            self.live_url = self.lives[self.current_live_index]
            self.set_media()
            self.start_live()

    def atualizar_live(self):
        nova_live = verificar_e_atualizar_live()

        if nova_live:
            self.live_url = nova_live
            self.lives = [nova_live]
            self.current_live_index = 0

            # 🔁 Sempre reinicia a mídia, mesmo que a URL seja a mesma
            self.player.stop()
            self.set_media()

            # Destroi o player atual
            self.player.stop()
            self.player.deleteLater()

            # Cria um novo player do zero
            self.player = QMediaPlayer(self)
            self.audio_output = QAudioOutput()
            self.audio_output.setVolume(0.0)
            self.player.setAudioOutput(self.audio_output)
            self.player.setVideoOutput(self.video_item)

            # Reconfigura a mídia e inicia
            self.set_media()
            QTimer.singleShot(500, self.start_live)

    def verificar_live(self):
        if self.reconectando or not self.internet_conectada:
            return

        self.reconectando = True  # 🔒 bloqueia até a verificação acabar

        self.verifier_thread = LiveVerifierThread(self.player)
        self.verifier_thread.resultado.connect(self._verificacao_finalizada)
        self.verifier_thread.finished.connect(lambda: setattr(self, "reconectando", False))  # 🔓 libera depois
        self.verifier_thread.start()


    def _verificacao_finalizada(self, funcionando):
        if funcionando:
            self.verificacoes_paradas = 0
        else:
            self.verificacoes_paradas += 1
            print(f"⚠️ Live travada ({self.verificacoes_paradas}/3)")
            if self.verificacoes_paradas >= 3:
                print("🔁 Live travada. Recarregando...")
                self.verificacoes_paradas = 0
                self.reconectar()
                self.atualizar_live()

    def verificar_conexao_internet(self):
        try:
            socket.create_connection(("1.1.1.1", 53), timeout=1)
            if not self.internet_conectada:
                print("✅ Internet voltou. Aguardando estabilização para reconectar a live...")
                self.internet_conectada = True
                self.reconectando = True  # previne avalanche de reconexões

                QTimer.singleShot(3000, lambda: (
                    self.atualizar_live(),
                    setattr(self, "reconectando", False)
                ))
        except OSError:
            if self.internet_conectada:
                print("❌ Internet caiu.")
            self.internet_conectada = False


    def reconectar(self):
        self.player.stop()
        self.reconectar_thread = LiveReconnectThread(self)
        self.reconectar_thread.finished.connect(lambda: setattr(self, "reconectando", False))
        self.reconectando = True
        self.reconectar_thread.start()


