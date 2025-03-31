# 🖥️ DevTelas Software — Sistema de Exibição em NUCs

Aplicação que roda localmente em mini PCs (NUCs), responsável por exibir o conteúdo das telas em condomínios e empresas. Trabalha de forma **autônoma**, com atualização remota e funcionamento offline.

---

## 🧠 Principais Recursos

- Exibição de:
  - 📰 Notícias com QR Code e contagem de acessos
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

> Em breve: guia passo a passo para instalação em NUCs novos (primeiro boot, configuração automática, dependências, etc.)

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
