import os
import json
import random
from itertools import cycle
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import QUrl, Qt, QTimer
import glob


def has_new_videos(current_list, folder):
    current_files = set(os.path.basename(p) for p in current_list)
    all_files = set(os.path.basename(p) for p in glob.glob(os.path.join(folder, "**/*.mp4"), recursive=True))
    return not current_files.issuperset(all_files)


class VideoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.json_path = "cache/update.json"
        self.entretenimento_json = "cache/entretenimento_update.json"
        self.folder_propagandas = "cache"
        self.folder_entretenimento = "cache/Entretenimento"
        self.last_snapshot = self.get_folder_snapshot()

        # Player setup
        self.video_widget = QVideoWidget()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(None)
        self.player.setVideoOutput(self.video_widget)

        # Layout setup
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(0)
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_widget.setMinimumSize(1, 1)
        self.video_widget.setAspectRatioMode(Qt.AspectRatioMode.IgnoreAspectRatio)
        self.video_widget.setStyleSheet("""
            QVideoWidget {
                border-radius: 20px;
                background-color: black;
            }
        """)
        layout.addWidget(self.video_widget)
        self.setLayout(layout)

        # Video list
        self.video_list = self.get_videos_from_json()
        self.current_video_index = 0
        if self.video_list:
            self.play_video(self.video_list[self.current_video_index])
        else:
            print("⚠️ Nenhum vídeo encontrado!")

        # Signals
        self.player.mediaStatusChanged.connect(self.handle_video_end)
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_video_list)
        self.update_timer.start(10000)  # 10 segundos

    def get_folder_snapshot(self):
        """Retorna um snapshot (nome + data modificação) dos arquivos de vídeo."""
        paths = []
        for folder in [
            os.path.join(self.folder_propagandas, "Propagandas"),
            os.path.join(self.folder_entretenimento, "curiosidades"),
            os.path.join(self.folder_entretenimento, "engracados"),
            os.path.join(self.folder_entretenimento, "enigmas"),
        ]:
            if os.path.exists(folder):
                for f in os.listdir(folder):
                    full_path = os.path.join(folder, f)
                    if os.path.isfile(full_path):
                        paths.append((f, os.path.getmtime(full_path)))
        return set(paths)


    def get_videos_from_json(self):
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                json_propagandas = json.load(f)
            with open(self.entretenimento_json, "r", encoding="utf-8") as f:
                json_entretenimento = json.load(f)

            def listar_videos(lista, base, categoria=None):
                videos = []
                for item in lista:
                    if item.get("status") == "deleted":
                        continue
                    if categoria and item.get("categoria") != categoria:
                        continue
                    caminho = os.path.join(base, item["video"])
                    if os.path.exists(caminho):
                        videos.append(caminho)
                    else:
                        print(f"⚠️ Arquivo ausente: {caminho}")
                return videos

            propagandas = listar_videos(json_propagandas.get("Propagandas", []), self.folder_propagandas)
            curiosidades = listar_videos(json_entretenimento["entretenimento"], self.folder_entretenimento, "curiosidades")
            engracados = listar_videos(json_entretenimento["entretenimento"], self.folder_entretenimento, "engracados")
            enigmas = listar_videos(json_entretenimento["entretenimento"], self.folder_entretenimento, "enigmas")

            random.shuffle(curiosidades)
            random.shuffle(engracados)
            random.shuffle(enigmas)

            intercalados = []
            prop_cycle = cycle(propagandas) if propagandas else None
            while curiosidades or engracados or enigmas:
                if curiosidades and prop_cycle:
                    intercalados.append(next(prop_cycle))
                    intercalados.append(curiosidades.pop(0))
                if engracados and prop_cycle:
                    intercalados.append(next(prop_cycle))
                    intercalados.append(engracados.pop(0))
                if enigmas and prop_cycle:
                    intercalados.append(next(prop_cycle))
                    intercalados.append(enigmas.pop(0))

            if not intercalados and propagandas:
                intercalados = propagandas

            return intercalados

        except Exception as e:
            print(f"❌ Erro ao processar JSON: {e}")
            return []

    def update_video_list(self):
        new_snapshot = self.get_folder_snapshot()
        if new_snapshot != self.last_snapshot:
            print("🔄 Alterações detectadas nos arquivos. Atualizando lista de vídeos...")
            self.last_snapshot = new_snapshot
            new_list = self.get_videos_from_json()
            if new_list != self.video_list:
                self.video_list = new_list
                current = os.path.normpath(self.player.source().toLocalFile())
                norm_list = [os.path.normpath(p) for p in self.video_list]
                if current not in norm_list:
                    self.current_video_index = 0
                    self.play_video(self.video_list[0])


    def play_video(self, video_path):
        if os.path.exists(video_path):
            self.player.setSource(QUrl.fromLocalFile(video_path))
            self.player.play()
        else:
            print(f"⚠️ Vídeo não encontrado: {video_path}. Atualizando lista...")
            self.video_list = self.get_videos_from_json()
            self.current_video_index = 0
            if self.video_list:
                self.play_video(self.video_list[0])

    def handle_video_end(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.current_video_index += 1
            if self.current_video_index >= len(self.video_list):
                print("🔁 Reiniciando playlist...")
                self.current_video_index = 0
            self.play_video(self.video_list[self.current_video_index])
