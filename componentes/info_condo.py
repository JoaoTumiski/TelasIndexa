import os
import json
import datetime
import pypdfium2
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QWidget, QSizePolicy
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer


class InfoWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.last_json_data = None

        # ⏱️ Timer de checagem de atualizações do JSON
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.check_for_json_update)
        self.update_timer.start(10000)  # 🔄 Verifica a cada 10 segundos

        # 📌 Caminho do JSON extraído
        self.json_path = "cache/update.json"
        self.notices_folder = "cache/CondominiumNotices/"
        self.default_image = "assets/no_notices.png"

        # 📌 Layout principal
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 📌 Criar título fixo
        self.title_label = QLabel("Notícias do Condomínio")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setFixedWidth(540)
        self.title_label.setStyleSheet("""
            background-color: #7B1FA2;
            color: white;
            font-size: 24px;
            font-weight: bold;
            border-top-left-radius: 15px;
            border-top-right-radius: 15px;
            padding: 10px;
        """)

        # 📌 Criar QLabel para exibir imagens e PDFs convertidos
        self.bg_label = QLabel(self)
        self.bg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bg_label.setFixedHeight(740)
        self.bg_label.setFixedWidth(540)
        self.bg_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.bg_label.setScaledContents(True)
        self.bg_label.setStyleSheet("border-bottom-left-radius: 15px; border-bottom-right-radius: 15px;")

        # 📌 Adicionar widgets ao layout
        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.bg_label)
        self.setLayout(main_layout)

        # 📌 Carregar avisos do condomínio
        self.notices = self.get_valid_notices()
        self.current_notice_index = 0
        self.current_pdf_page = 0  # 🔹 Página atual do PDF

        # 📌 Criar timers de aviso e PDF (mas só iniciar se houver avisos)
        self.notice_timer = QTimer(self)
        self.notice_timer.timeout.connect(self.next_notice)

        self.page_timer = QTimer(self)
        self.page_timer.timeout.connect(self.next_pdf_page)

        if self.notices:
            self.update_notice()
            self.notice_timer.start(15000)
            self.page_timer.start(5000)
        else:
            self.show_default_image()

            self.check_for_json_update()

    def check_for_json_update(self):
        """Verifica se houve mudança no JSON e recarrega os avisos se necessário."""
        if not os.path.exists(self.json_path):
            return

        try:
            with open(self.json_path, "r", encoding="utf-8") as file:
                new_json_raw = file.read()

            if new_json_raw == self.last_json_data:
                return  # nada mudou
            print("🔄 JSON alterado! Recarregando avisos...")

            # Salva novo JSON
            self.last_json_data = new_json_raw
            new_json_data = json.loads(new_json_raw)

            # Atualiza a lista de avisos
            new_notices = self.get_valid_notices()

            # Se a lista mudou, aplica as alterações
            if new_notices != self.notices:
                self.notices = new_notices
                self.current_notice_index = 0
                self.current_pdf_page = 0

                if self.notices:
                    self.update_notice()
                    self.notice_timer.start()
                    self.page_timer.start()
                else:
                    self.show_default_image()
                    self.notice_timer.stop()
                    self.page_timer.stop()

            # ✅ Agora podemos deletar os arquivos marcados como 'deleted' com atraso
            QTimer.singleShot(10000, lambda: self.delete_removed_notices(new_json_data))


        except Exception as e:
            print(f"❌ Erro ao verificar mudanças no JSON: {e}")

    def get_valid_notices(self):
        """Obtém avisos vigentes do JSON."""
        if not os.path.exists(self.json_path):
            print(f"⚠️ Arquivo JSON não encontrado: {self.json_path}")
            return []

        try:
            with open(self.json_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                notices = data.get("CondominiumNotices", [])

                today = datetime.date.today()
                valid_notices = []

                for notice in notices:
                    # 🔒 Ignora avisos marcados como 'deleted'
                    if notice.get("status") == "deleted":
                        continue

                    # 🔒 Verifica se os campos necessários existem
                    if not all(k in notice for k in ("data_ini", "data_fim", "mensagem")):
                        print(f"⚠️ Aviso incompleto ignorado: {notice}")
                        continue

                    try:
                        data_ini = datetime.datetime.strptime(notice["data_ini"], "%Y-%m-%d").date()
                        data_fim = datetime.datetime.strptime(notice["data_fim"], "%Y-%m-%d").date()

                        if data_ini <= today <= data_fim:
                            file_name = os.path.basename(notice["mensagem"])
                            file_path = os.path.join(self.notices_folder, file_name)

                            if os.path.exists(file_path):
                                valid_notices.append(file_path)
                            else:
                                print(f"⚠️ Arquivo do aviso não encontrado: {file_path}")
                    except Exception as date_error:
                        print(f"⚠️ Erro ao processar datas do aviso: {notice} | Erro: {date_error}")

                return valid_notices

        except Exception as e:
            print(f"❌ Erro ao processar JSON: {e}")
            return []

    def update_notice(self):
        """Atualiza a exibição com a imagem ou renderiza o PDF."""
        if self.notices:
            file_path = self.notices[self.current_notice_index]

            if file_path.endswith((".png", ".jpg", ".jpeg")):
                pixmap = QPixmap(file_path)
                self.bg_label.setPixmap(pixmap.scaled(
                    self.bg_label.width(), self.bg_label.height(),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                ))
                self.bg_label.show()

            elif file_path.endswith(".pdf"):
                self.current_pdf_page = 0  # 🔹 Reinicia para a primeira página
                self.render_pdf(file_path, self.current_pdf_page)  # 📌 Renderiza a primeira página

        else:
            self.show_default_image()
            

    def delete_removed_notices(self, json_data):
        """Deleta arquivos marcados como 'deleted' no JSON após atualização da interface."""

        # 🧹 Remove imagem temporária primeiro
        if os.path.exists("temp_pdf.png"):
            try:
                os.remove("temp_pdf.png")
                print("🧹 Imagem temporária removida.")
            except Exception as e:
                print(f"⚠️ Erro ao remover temp_pdf.png: {e}")

        notices = json_data.get("CondominiumNotices", [])

        for notice in notices:
            if notice.get("status") == "deleted":
                file_name = os.path.basename(notice.get("mensagem", ""))
                file_path = os.path.join(self.notices_folder, file_name)

                if os.path.exists(file_path):
                    # ⛔️ Evita deletar o arquivo que está sendo exibido no momento
                    current_file = self.notices[self.current_notice_index] if self.notices else ""
                    if os.path.abspath(file_path) == os.path.abspath(current_file):
                        print(f"⏩ Ignorando exclusão do aviso atual em exibição: {file_path}")
                        continue

                    try:
                        os.remove(file_path)
                        print(f"🗑️ Arquivo deletado: {file_path}")
                    except Exception as e:
                        print(f"❌ Erro ao deletar {file_path}: {e}")

    def next_notice(self):
        """Alterna para o próximo aviso no loop"""
        self.current_notice_index = (self.current_notice_index + 1) % len(self.notices)
        self.update_notice()

    def next_pdf_page(self):
        """Alterna entre as páginas do PDF"""
        if self.notices and self.notices[self.current_notice_index].endswith(".pdf"):
            pdf_path = self.notices[self.current_notice_index]
            pdf = pypdfium2.PdfDocument(pdf_path)

            if self.current_pdf_page < len(pdf) - 1:  # 🔹 Correção do método
                self.current_pdf_page += 1  # 🔹 Vai para a próxima página
            else:
                self.current_pdf_page = 0  # 🔹 Volta para a primeira página

            self.render_pdf(pdf_path, self.current_pdf_page)

    def render_pdf(self, pdf_path, page_num=0):
        """Renderiza uma página do PDF e exibe como imagem usando `pypdfium2`"""
        if not os.path.exists(pdf_path):
            print(f"⚠️ Arquivo PDF não encontrado: {pdf_path}")
            return

        try:
            pdf = pypdfium2.PdfDocument(pdf_path)
            page = pdf[page_num]  # Página selecionada
            pil_image = page.render(scale=2).to_pil()

            # Salva como imagem temporária
            temp_image_path = "temp_pdf.png"
            pil_image.save(temp_image_path, "PNG")

            # Libera o documento após uso
            del page
            pdf.close()

            pixmap = QPixmap(temp_image_path)
            self.bg_label.setPixmap(pixmap.scaled(
                self.bg_label.width(), self.bg_label.height(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            ))
            self.bg_label.show()

        except Exception as e:
            print(f"❌ Erro ao renderizar PDF: {e}")


    def show_default_image(self):
        """Exibe a imagem padrão quando não há avisos ativos"""
        pixmap = QPixmap(self.default_image)
        if pixmap.isNull():
            print("⚠️ Erro: Imagem padrão 'no_notices.png' não encontrada!")
        else:
            self.bg_label.setPixmap(pixmap.scaled(
                self.bg_label.width(), self.bg_label.height(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            ))
        self.bg_label.show()
