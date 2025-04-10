import os
import json
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import QUrl, Qt, QTimer
import glob
from itertools import cycle


def has_new_videos(current_list, folder):
    current_files = set(os.path.basename(p) for p in current_list)
    all_files = set(os.path.basename(p) for p in glob.glob(os.path.join(folder, "**/*.mp4"), recursive=True))
    return not current_files.issuperset(all_files)

class VideoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.entretenimento_json = "cache/entretenimento_update.json"
        self.json_path = "cache/update.json"
        self.video_folder_propagandas = "cache/Propagandas"
        self.video_folder_entretenimento = "cache/Entretenimento"


        # 📌 Layout para organizar o vídeo
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(0)

        # 📌 Criar o player de vídeo
        self.video_widget = QVideoWidget()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(None)  # 🔹 Desativa o áudio para evitar conflito

        self.player.setVideoOutput(self.video_widget)

        # 📌 Ajustar para ocupar toda a tela
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_widget.setMinimumSize(1, 1)
        self.video_widget.setAspectRatioMode(Qt.AspectRatioMode.IgnoreAspectRatio)

        # 📌 Aplicar bordas arredondadas ao próprio `QVideoWidget`
        self.video_widget.setStyleSheet("""
            QVideoWidget {
                border-radius: 20px;
                background-color: black;
            }
        """)

        # 📌 Adicionar o vídeo ao layout
        layout.addWidget(self.video_widget)
        self.setLayout(layout)

        # 📌 Carregar a lista de vídeos do JSON
        self.video_list = self.get_videos_from_json()
        self.current_video_index = 0

        if self.video_list:
            self.play_video(self.video_list[self.current_video_index])
        else:
            print("⚠️ Nenhum vídeo encontrado!")

        # 📌 Conectar evento para trocar de vídeo quando terminar
        self.player.mediaStatusChanged.connect(self.handle_video_end)

        # 📌 Criar Timer para monitorar mudanças no JSON
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_video_list)
        self.update_timer.start(10000)  # Verifica a cada 10 segundos

    def update_video_list(self):
        """Verifica se houve mudanças no JSON ou arquivos físicos e atualiza a lista de reprodução."""
        new_video_list = self.get_videos_from_json()

        arquivos_novos = has_new_videos(self.video_list, self.video_folder_propagandas)

        if new_video_list != self.video_list or arquivos_novos:
            print("🔄 Atualizando lista de vídeos (JSON ou novos arquivos detectados)...")
            self.video_list = new_video_list
            self.current_video_index = 0  # Reinicia o índice

            # 🔹 Se o vídeo atual não estiver mais na lista, troca para o primeiro disponível
            if not self.video_list or (self.player.source().toLocalFile() not in self.video_list):
                print("▶️ Trocando vídeo pois o atual foi removido ou a lista foi recriada.")
                self.play_video(self.video_list[0] if self.video_list else None)

    def stop_and_release_video(self):
        """Para a reprodução do vídeo e libera o arquivo para exclusão."""
        self.player.stop()  # Para o vídeo
        self.player.setSource(QUrl())  # Remove a referência ao arquivo


    def get_videos_from_json(self):
        """Intercala: propaganda → curiosidade → propaganda → engraçado → propaganda → enigma"""
        if not os.path.exists(self.json_path):
            print(f"⚠️ Arquivo JSON não encontrado: {self.json_path}")
            return []

        try:
            # 🔹 Carrega propagandas do update.json
            with open(self.json_path, "r", encoding="utf-8") as file:
                data_propagandas = json.load(file)

            # 🔹 Carrega entretenimento do JSON separado
            if os.path.exists(self.entretenimento_json):
                with open(self.entretenimento_json, "r", encoding="utf-8") as f:
                    data_entretenimento = json.load(f)
            else:
                data_entretenimento = {"entretenimento": []}

            def listar_videos_por_categoria(lista_json, base_folder, categoria_desejada=None):
                validos = []
                deletados = []

                for item in lista_json:
                    if item.get("status") == "deleted":
                        continue

                    categoria = item.get("categoria")
                    if categoria_desejada and categoria != categoria_desejada:
                        continue

                    nome_arquivo = os.path.basename(item.get("video", ""))
                    caminho = os.path.join(base_folder, categoria or "", nome_arquivo)

                    if os.path.exists(caminho):
                        validos.append(caminho)
                    else:
                        print(f"⚠️ Arquivo ausente: {caminho}")

                return validos

            propagandas = listar_videos_por_categoria(data_propagandas.get("Propagandas", []), self.video_folder_propagandas)
            curiosidades = listar_videos_por_categoria(data_entretenimento.get("entretenimento", []), self.video_folder_entretenimento, "curiosidades")
            engracados   = listar_videos_por_categoria(data_entretenimento.get("entretenimento", []), self.video_folder_entretenimento, "engracados")
            enigmas      = listar_videos_por_categoria(data_entretenimento.get("entretenimento", []), self.video_folder_entretenimento, "enigmas")


            # 🔁 Intercala conforme ciclo definido
            intercalados = []
            propaganda_cycle = cycle(propagandas) if propagandas else None

            categorias = [curiosidades, engracados, enigmas]
            i = 0
            while any(categorias):
                atual = categorias[i % 3]
                if atual:
                    if propaganda_cycle:
                        intercalados.append(next(propaganda_cycle))
                    intercalados.append(atual.pop(0))
                i += 1

            # Caso só tenha propagandas ou só entretenimento
            if not intercalados:
                intercalados = propagandas + curiosidades + engracados + enigmas

            return intercalados

        except Exception as e:
            print(f"❌ Erro ao processar JSON: {e}")
            return []

    def play_video(self, video_path):
        """Reproduz o vídeo selecionado"""
        if os.path.exists(video_path):
            self.player.setSource(QUrl.fromLocalFile(video_path))
            self.player.play()
        else:
            print(f"⚠️ Vídeo não encontrado: {video_path}. Atualizando lista...")
            self.video_list = self.get_videos_from_json()
            self.current_video_index = 0
            if self.video_list:
                self.play_video(self.video_list[self.current_video_index])

    def handle_video_end(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.current_video_index += 1

            if self.current_video_index >= len(self.video_list):
                print("🔄 Reiniciando a lista de vídeos...")
                self.current_video_index = 0

            if self.video_list:
                self.play_video(self.video_list[self.current_video_index])
            else:
                print("⚠️ Lista de vídeos vazia após reinício.")

