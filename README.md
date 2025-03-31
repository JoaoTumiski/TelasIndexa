# 🖥️  Software — Sistema de Exibição em NUCs

Aplicação que roda localmente em mini PCs (NUCs), responsável por exibir o conteúdo das telas em condomínios e empresas. Trabalha de forma **autônoma**, com atualização remota e funcionamento offline.

---

## 🧠 Principais Recursos

- Exibição de:
  - 📰 Notícias com QR Code 
  - 📢 Avisos do condomínio
  - 📹 Live e câmeras ao vivo (com reconexão)
  - 🎬 Vídeos institucionais e propagandas
  - 💰 Cotações do dia
    
- Funcionamento offline com cache em **SQLite**
- Atualização automática de conteúdo a cada 20 minutos
- Verificação da versão via JSON
- Requisições otimizadas e mínimo consumo de dados

---

## 🛠️ Requisitos do Sistema

- Windows ou Linux
- Python 3.11+
- Internet para atualizações (mínimo 512kbps)
- Conexão com API FastAPI no EC2

---

## ⚙️ Instalação

Este guia descreve o processo completo para instalação e configuração do sistema DevTelas em NUCs com Windows 10 ou 11. O objetivo é garantir que o player inicie automaticamente, funcione de forma estável e permita acesso remoto e manutenção.

---

## 🧰 Requisitos Iniciais

- NUC com suporte a Windows 10 ou 11
- Pendrive bootável com ISO do Windows
- Conexão com a internet
- Conta no GitHub com acesso ao repositório do DevTelas
- Acesso ao instalador do Deep Freeze

---

## ⚙️ Etapas de Instalação

### 1️⃣ Instalar o Windows 10 ou 11

1. Inicie o NUC pelo pendrive bootável.
2. Siga o processo normal de instalação do Windows.
3. Crie apenas **uma partição principal** no disco (iremos dividir depois).
4. Finalize a instalação e conecte o dispositivo à internet.

---

### 2️⃣ Instalar e configurar o AnyDesk

1. Baixe o AnyDesk em: [https://anydesk.com/pt/downloads](https://anydesk.com/pt/downloads)
2. Instale normalmente.
3. Faça login com a conta padrão da equipe.
4. Vá em **Configurações > Segurança**:
   - Ative **Acesso não supervisionado**.
   - Defina uma senha de acesso.
   - Permita controle total do dispositivo.

✅ O AnyDesk deve estar **logado e pronto para acesso remoto mesmo após reinicializações**.

---

### 3️⃣ Instalar o Python com PATH

1. Baixe o instalador do Python 3.11+ em: [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Marque a opção **“Add Python to PATH”** no início da instalação.
3. Conclua a instalação.

⚠️ Verifique com `python --version` no terminal (cmd) se a instalação está correta.

---

### 4️⃣ Configurar o Deep Freeze com partição não congelada

1. Crie uma **nova partição no disco** com pelo menos **16 GB** (via Gerenciamento de Disco).
2. Instale o **Deep Freeze** e selecione:
   - A partição principal (C:) como **Freezada (congelada)**
   - A nova partição (ex: D:) como **Não congelada**

3. Conclua a instalação e reinicie o NUC.
4. Verifique se apenas o disco D: está com escrita persistente.

---

### 5️⃣ Clonar o software DevTelas no disco não congelado

1. Acesse o disco **não congelado** (ex: D:)
2. Abra o terminal e clone o projeto:
3. `git clone https://github.com/JoaoTumiski/TelasIndexa.git`
4. Navegue até a pasta e instale os requisitos (se necessário):
   - `cd telas-software`
   - `pip install -r requirements.txt`

### 6️⃣ Iniciar o software automaticamente com o sistema

1.Pressione Win + R, digite:
- `shell:startup`
2. Cole o atalho lá. Isso fará com que o software inicie toda vez que o sistema for ligado.

  ---

## 🔄 Estrutura de Atualizações

- O software verifica se há nova versão no servidor (EC2)
- Se houver, baixa e substitui os arquivos necessários
- A versão local é registrada em `version.json`
- Funciona 100% offline após atualização bem-sucedida

---

## 🧭 Roadmap Software

- [ ] Sistema de logs com envio automático
- [ ] Tela de debug local com status da internet/API
- [ ] Instalação automatizada com script `.bat` ou `.sh`

---

👉 [Acesse aqui o repositório do Servidor AWS ](https://github.com/JoaoTumiski/ServerIndexa)

---
