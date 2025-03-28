import os
import json
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import QUrl, Qt, QTimer


class VideoWidget(QWidget):
    def __init__(self):
        super().__init__()
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
        """Verifica se houve mudanças no JSON e atualiza a lista de reprodução."""
        new_video_list = self.get_videos_from_json()

        if new_video_list != self.video_list:  # 🔹 Só atualiza se houver mudanças
            print("🔄 Atualizando lista de vídeos...")
            self.video_list = new_video_list
            self.current_video_index = 0  # Reinicia o índice

            # 🔹 Se o vídeo atual não estiver mais na lista, troca para o primeiro disponível
            if not self.video_list or (self.player.source().toLocalFile() not in self.video_list):
                print("▶️ Trocando vídeo pois o atual foi removido.")
                self.play_video(self.video_list[0] if self.video_list else None)

    def stop_and_release_video(self):
        """Para a reprodução do vídeo e libera o arquivo para exclusão."""
        self.player.stop()  # Para o vídeo
        self.player.setSource(QUrl())  # Remove a referência ao arquivo


    def get_videos_from_json(self):
        """Obtém todos os vídeos de Propagandas e Entretenimento, intercalando na ordem."""
        if not os.path.exists(self.json_path):
            print(f"⚠️ Arquivo JSON não encontrado: {self.json_path}")
            return []

        try:
            with open(self.json_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            def listar_validos(categoria, pasta):
                validos = []
                deletados = []
                for item in data.get(categoria, []):
                    video_nome = os.path.basename(item.get("video", ""))
                    video_path = os.path.join(pasta, video_nome)

                    if item.get("status") == "deleted":
                        if os.path.exists(video_path):
                            deletados.append(video_path)
                    elif os.path.exists(video_path):
                        validos.append(video_path)
                    else:
                        print(f"⚠️ Arquivo ausente: {video_path}")
                return validos, deletados

            propagandas, deletar_p1 = listar_validos("Propagandas", self.video_folder_propagandas)
            entretenimentos, deletar_p2 = listar_validos("Entretenimento", self.video_folder_entretenimento)

            # 🔁 Intercalar os vídeos das duas listas
            intercalados = []
            for i in range(max(len(propagandas), len(entretenimentos))):
                if i < len(propagandas):
                    intercalados.append(propagandas[i])
                if i < len(entretenimentos):
                    intercalados.append(entretenimentos[i])

            # Excluir os deletados (se houver)
            deletados = deletar_p1 + deletar_p2
            if deletados:
                self.stop_and_release_video()
                for file in deletados:
                    try:
                        os.remove(file)
                        print(f"🗑️ Vídeo deletado: {file}")
                    except Exception as e:
                        print(f"❌ Erro ao deletar {file}: {e}")

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
        """Muda para o próximo vídeo quando um termina"""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.current_video_index += 1

            if self.current_video_index >= len(self.video_list):
                print("🔄 Reiniciando a lista de vídeos...")
                self.current_video_index = 0  # Reinicia do primeiro vídeo

            self.play_video(self.video_list[self.current_video_index])
