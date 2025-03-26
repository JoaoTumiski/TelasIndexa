import os
import json
import sys
import ctypes
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import QTimer, Qt
from config.database import supabase
# 🧠 Caminho do VLC portable dentro do projeto
vlc_base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "vlc"))
libvlc_path = os.path.join(vlc_base, "libvlc.dll")
plugins_path = os.path.join(vlc_base, "plugins")

# 🔧 Força carregamento do VLC portable
if os.path.exists(libvlc_path):
    os.environ["PATH"] += os.pathsep + vlc_base
    os.environ["VLC_PLUGIN_PATH"] = plugins_path
    ctypes.CDLL(libvlc_path)
else:
    print("❌ libvlc.dll não encontrada no VLC portable.")
    
import vlc


# 🔥 Caminho do JSON local
LIVE_JSON_PATH = "cache/live.json"
# 🔥 Caminho do arquivo de configuração
CONFIG_PATH = "config.json"

def carregar_config():
    """Carrega o ID do cliente a partir do arquivo config.json"""
    if not os.path.exists(CONFIG_PATH):
        print(f"❌ Arquivo de configuração não encontrado: {CONFIG_PATH}")
        return None

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            config_data = json.load(file)
            return int(config_data.get("tela_id", 102))  # Retorna 102 se não encontrar

    except Exception as e:
        print(f"❌ Erro ao carregar config.json: {e}")
        return 000  # Retorna um ID padrão caso haja erro

# 🔹 Agora definimos o CLIENTE_ID dinamicamente
CLIENTE_ID = carregar_config()
print(f"✅ Cliente ID carregado: {CLIENTE_ID}")  # Debug para garantir que carregou


def obter_live_supabase():
    """Busca a live mais recente do Supabase para o cliente específico"""
    try:
        response = supabase.table("cameras").select("url, data_criacao").eq("cliente_id", CLIENTE_ID).order("data_criacao", desc=True).limit(1).execute()

        if response.data:
            live_data = response.data[0]
            return live_data["url"], live_data["data_criacao"]
        return None, None

    except Exception as e:
        print(f"⚠️ Erro ao buscar live no Supabase: {e}")
        return None, None

def salvar_live_localmente(url, data_criacao):
    """Salva a URL da live no arquivo local"""
    try:
        with open(LIVE_JSON_PATH, "w", encoding="utf-8") as file:
            json.dump({"url": url, "data_criacao": data_criacao}, file, indent=4, ensure_ascii=False)
        print(f"✅ Live salva em {LIVE_JSON_PATH}")
    except Exception as e:
        print(f"❌ Erro ao salvar live localmente: {e}")

def carregar_live_local():
    """Carrega a live salva localmente"""
    if not os.path.exists(LIVE_JSON_PATH):
        return None, None

    try:
        with open(LIVE_JSON_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data.get("url"), data.get("data_criacao")

    except Exception as e:
        print(f"❌ Erro ao carregar live local: {e}")
        return None, None

def verificar_e_atualizar_live():
    """Verifica se precisa atualizar a live e baixa um novo JSON se necessário"""
    print("🔄 Verificando atualização da live...")

    url_local, timestamp_local = carregar_live_local()
    response = supabase.table("cameras").select("url, data_criacao").eq("cliente_id", CLIENTE_ID).order("data_criacao", desc=True).execute()

    if response.data:
        lives_supabase = [(live["url"], live["data_criacao"]) for live in response.data]
        url_supabase = response.data[0]["url"]
        timestamp_supabase = lives_supabase[0][1]  # Pega a data da mais recente

        if timestamp_supabase != timestamp_local:
            print(f"🔄 Atualização encontrada! Novo timestamp: {timestamp_supabase}")
            salvar_live_localmente(url_supabase, timestamp_supabase)
            return url_supabase

    print("✅ Live já está atualizada. Nenhuma ação necessária.")
    return url_local if isinstance(url_local, list) else [url_local]  # Retorna sempre uma lista


class LiveWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 🔹 Buscar a live inicial (pode ser única ou uma lista)
        live_data = verificar_e_atualizar_live()
        if isinstance(live_data, list):
            self.lives = live_data
            self.live_url = self.lives[0] if self.lives else None
        else:
            self.live_url = live_data
            self.lives = [self.live_url] if self.live_url else []

        self.current_live_index = 0

        # 🔹 Criar layout para o player
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # 🔹 Criar um widget para exibir o vídeo
        self.video_frame = QLabel(self)
        self.video_frame.setStyleSheet("background-color: black;")
        self.video_frame.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.video_frame)

        # 🔹 Criar uma instância do VLC
        self.instance = vlc.Instance("--no-xlib","--avcodec-hw=none")
        self.player = self.instance.media_player_new()

        # 🔹 Integrar VLC ao widget do PyQt6
        if sys.platform.startswith("linux"):
            self.player.set_xwindow(self.video_frame.winId())
        elif sys.platform.startswith("win"):
            self.player.set_hwnd(self.video_frame.winId())

        # 🔹 Configurar a mídia com a primeira URL
        self.set_media()

        # 🔹 Criar um timer para iniciar a live após renderizar o widget
        self.start_timer = QTimer(self)
        self.start_timer.timeout.connect(self.start_live)
        self.start_timer.setSingleShot(True)
        self.start_timer.start(500)


    def apply_fixed_zoom(self):
        """Aplica um nível fixo de zoom na live"""
        fixed_zoom = 0.4  # 🔥 Defina o fator de zoom desejado (ex: 1.5, 2.0, etc.)
        self.player.video_set_scale(fixed_zoom)

        # 🔹 Criar um timer para verificar falhas e atualizar a live
        self.reconnect_timer = QTimer(self)
        self.reconnect_timer.timeout.connect(self.check_live_status)
        self.reconnect_timer.start(5000)  # Verifica a cada 5 segundos

        # 🔹 Criar um timer para trocar de live a cada 30 segundos se houver mais de uma
        if len(self.lives) > 1:
            self.switch_timer = QTimer(self)
            self.switch_timer.timeout.connect(self.switch_live)
            self.switch_timer.start(30000)  # 30 segundos

        # 🔹 Criar um timer para verificar atualizações a cada 20 minutos
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.atualizar_live)
        self.update_timer.start(1200000)  # 20 minutos

    def set_media(self, url=None):
        """Configura a URL da live no player"""
        if not url:
            url = self.live_url

        # Garante que estamos passando uma string, não uma lista
        if isinstance(url, list):
            url = url[0]

        if url:
            self.media = self.instance.media_new(url)
            self.player.set_media(self.media)
        else:
            print("⚠️ Nenhuma live disponível.")

    def start_live(self):
        """Inicia a transmissão da live dentro do widget"""
        if self.live_url:
            self.player.play()
            self.apply_fixed_zoom()  # 🔥 Aplica o zoom fixo sempre que a live inicia
        else:
            print("⚠️ Nenhuma live disponível para iniciar.")

    def check_live_status(self):
        """Verifica se a live está rodando e troca a mídia se houver erro"""
        state = self.player.get_state()

        if state in [vlc.State.Ended, vlc.State.Stopped, vlc.State.Error, vlc.State.NothingSpecial]:
            print("⚠️ Live caiu, tentando reconectar...")

            # 🔄 Se houver mais de uma live, tenta trocar para outra
            if len(self.lives) > 1:
                self.switch_live()
            elif self.lives:
                self.set_media(self.lives[self.current_live_index])
                self.start_live()
            else:
                print("❌ Nenhuma live disponível. Mantendo estado atual.")

    def switch_live(self):
        """Troca para a próxima live a cada 30 segundos"""
        if len(self.lives) > 1:
            self.current_live_index = (self.current_live_index + 1) % len(self.lives)
            print(f"🔄 Trocando para a próxima live: {self.lives[self.current_live_index]}")
            self.set_media(self.lives[self.current_live_index])
            self.start_live()
            self.apply_fixed_zoom()  # 🔥 Aplica o zoom fixo na nova live
        else:
            print("⚠️ Apenas uma live disponível. Não há troca.")

    def atualizar_live(self):
        """Atualiza a live verificando o Supabase"""
        print("🔄 Atualizando live no Player...")
        nova_live = verificar_e_atualizar_live()
        if nova_live and nova_live != self.live_url:
            self.live_url = nova_live
            self.set_media()
            self.start_live()
