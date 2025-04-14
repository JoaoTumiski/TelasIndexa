import os
import json
from PyQt6.QtWidgets import QLabel, QWidget, QHBoxLayout
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QTimer
from config.database import supabase

# 🔥 Caminho do JSON local
COTACAO_JSON_PATH = "cache/cotacao.json"

# 🔥 Criar pasta cache se não existir
os.makedirs("cache", exist_ok=True)

def obter_cotacao_supabase():
    if supabase is None:
        print("⚠️ Supabase não disponível. Pulando atualização de notícias.")
        return None, None

    try:
        response = supabase.table("cotacoes").select("valor, atualizado_em").eq("tipo", "cotacao").execute()
        if response.data:
            cotacao_data = response.data[0]
            return cotacao_data["valor"], cotacao_data["atualizado_em"]  # Retorna os valores
        print("⚠️ Nenhuma cotação encontrada no Supabase.")
        return None, None

    except Exception as e:
        print(f"❌ Erro ao buscar cotação no Supabase: {e}")
        return None, None


def salvar_cotacao_localmente(cotacao, atualizado_em):
    """Salva a cotação no arquivo local e adiciona prints para depuração."""
    try:
        with open(COTACAO_JSON_PATH, "w", encoding="utf-8") as file:
            json.dump({"cotacao": cotacao, "atualizado_em": atualizado_em}, file, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Erro ao salvar cotação localmente: {e}")


def carregar_cotacao_local():
    """Carrega o JSON salvo localmente e garante que está em formato de dicionário"""
    if not os.path.exists(COTACAO_JSON_PATH):
        return None, None

    try:
        with open(COTACAO_JSON_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)

            # 🚀 Verifica se o campo "cotacao" está salvo como string e converte para dicionário
            if isinstance(data.get("cotacao"), str):
                data["cotacao"] = json.loads(data["cotacao"])

            return data.get("cotacao"), data.get("atualizado_em")

    except Exception as e:
        print(f"❌ Erro ao carregar cotação local: {e}")
        return None, None

def verificar_e_atualizar_cotacao():

    # 🔥 Busca timestamp do JSON salvo localmente
    cotacao_local, timestamp_local = carregar_cotacao_local()

    # 🔥 Busca do Supabase
    cotacao_supabase, timestamp_supabase = obter_cotacao_supabase()

    # Se não houver cotação no Supabase, manter o que já existe localmente
    if not cotacao_supabase:
        return cotacao_local

    # Se os timestamps forem diferentes, atualiza o JSON local
    if timestamp_supabase != timestamp_local:
        print(f"🔄 Atualização detectada! Novo timestamp: {timestamp_supabase}")
        salvar_cotacao_localmente(cotacao_supabase, timestamp_supabase)
        return cotacao_supabase  # Retorna a nova cotação
    return cotacao_local  # Retorna a cotação já salva


class Footer(QWidget):
    def __init__(self):
        super().__init__()

        # 📌 Criar um widget container para o texto
        self.container = QWidget(self)
        self.container.setFixedHeight(100)  # 🔺 Altura do footer
        self.container.setStyleSheet("background: transparent;")

        # 📌 Criar o layout horizontal dentro do container
        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 📌 Criar o label do carrossel
        self.label = QLabel(self.container)
        self.label.setFont(QFont("Arial", 32))
        self.label.setStyleSheet("color: white; padding: 20px;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # 📌 Adicionar o label ao layout
        layout.addWidget(self.label)

        # 📌 Carregar as cotações do JSON
        self.texts = self.get_cotacoes_from_json()
        self.update_label_text()

        # 📌 Criar um timer para fazer o texto rolar
        self.offset = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.scroll_text)
        self.timer.start(10)

        self.atualizar_cotacoes()

        # 🔥 Criar um timer para verificar atualizações a cada 20 minutos
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.atualizar_cotacoes)
        self.update_timer.start(1200000)  # 20 minutos (1.200.000 ms)

    def get_cotacoes_from_json(self):
        """Obtém as cotações do JSON salvo localmente."""
        cotacao, _ = carregar_cotacao_local()
        
        if not cotacao:
            return ["Cotações não disponíveis"]

        # 🔥 Converter JSON string para dicionário caso esteja salvo como string
        if isinstance(cotacao, str):
            cotacao = json.loads(cotacao)

        cotacoes_gerais = []
        
        # 🔹 Cotação da AwesomeAPI (com variação)
        for sigla, item in cotacao.get("awesomeapi", {}).items():
            nome = item.get("nome", sigla)
            compra = item.get("compra", "-")
            venda = item.get("venda", "-")
            variacao = item.get("variacao", "0")

            # 🔹 Definir setas 🔻🔺 com base na variação
            cor = "🔻" if "-" in variacao else "🔺"

            # 🔹 Formatar a string corretamente
            cotacoes_gerais.append(f"{nome}: Compra R$ {compra} | Venda R$ {venda} {cor} {variacao}%")

        # 🔹 Cotações da Ápice Câmbio
        cotacoes_apice = ["@Apice Câmbio:"]  # Prefixo para separação
        for item in cotacao.get("apice_cambios", []):
            moeda = item.get("moeda", "Desconhecido")
            compra = item.get("compra", "-")
            venda = item.get("venda", "-")
            cotacoes_apice.append(f"{moeda}: Compra R$ {compra} | Venda R$ {venda}")

        # 🔹 Juntar tudo (AwesomeAPI primeiro, depois Ápice)
        cotacoes = cotacoes_gerais + cotacoes_apice

        return cotacoes if cotacoes else ["Cotações não disponíveis"]


    def update_label_text(self):
        """Atualiza o texto do label com as cotações."""
        base_text = " | ".join(self.texts)
        self.current_text = f"{base_text}   |   {base_text}"
        self.label.setText(self.current_text)

        text_width = self.label.fontMetrics().boundingRect(self.current_text).width()
        self.label.setFixedWidth(text_width)

    def atualizar_cotacoes(self):
        """Atualiza as cotações verificando o Supabase e atualiza o label."""
        print("🔄 Atualizando cotações no Footer...")
        nova_cotacao = verificar_e_atualizar_cotacao()
        if nova_cotacao:
            self.texts = self.get_cotacoes_from_json()
            self.update_label_text()

    def scroll_text(self):
        """Move o texto continuamente, sem pausas"""
        self.offset -= 2
        text_width = self.label.fontMetrics().boundingRect(self.current_text).width() // 2

        if self.offset < -text_width:
            self.offset = 0

        self.label.move(self.offset, self.label.y())

    def resizeEvent(self, event):
        """Ajusta a posição inicial do texto ao redimensionar a janela"""
        self.container.setFixedWidth(self.width())
        super().resizeEvent(event)
