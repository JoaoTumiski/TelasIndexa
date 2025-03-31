# 📺 DevTelas — Sistema de Gestão de Conteúdo para Telas Inteligentes

Sistema inteligente para gerenciamento remoto de conteúdo em telas digitais instaladas em elevadores, condomínios, empresas e prédios comerciais. Desenvolvido para operar tanto **online** quanto **offline**, com atualizações automáticas e integração com diversos serviços na nuvem.

---

## 📌 Índice

- [🚀 Visão Geral](#-visão-geral)
- [🧠 Arquitetura do Sistema](#-arquitetura-do-sistema)
- [☁️ Infraestrutura na Nuvem](#-infraestrutura-na-nuvem)
- [🧩 Componentes do Sistema](#-componentes-do-sistema)
- [📡 Funcionamento Offline](#-funcionamento-offline)
- [📦 Atualizações e Versionamento](#-atualizações-e-versionamento)
- [🛠️ Backend (API)](#-backend-api)
- [📁 Gerenciamento de Arquivos](#-gerenciamento-de-arquivos)
- [🔐 Segurança e Estabilidade](#-segurança-e-estabilidade)
- [📊 Monitoramento e Logs](#-monitoramento-e-logs)
- [⚙️ Deploy e Automação](#-deploy-e-automação)
- [🧭 Roadmap Futuro](#-roadmap-futuro)
- [📄 Licença](#-licença)

---

## 🚀 Visão Geral

O **DevTelas** tem como objetivo facilitar o controle e a atualização de conteúdos multimídia exibidos em telas, sem depender de intervenções físicas. A solução é ideal para empresas que buscam praticidade, personalização e integração com sistemas modernos de conteúdo.

---

## 🧠 Arquitetura do Sistema

- Backend com **FastAPI**
- API hospedada em **AWS EC2 (Ubuntu 24.04)**
- Banco local: **SQLite** (modo offline)
- Banco remoto: **Firebase Firestore** e/ou **Supabase**
- Armazenamento de arquivos em **S3**
- Monitoramento de alterações via **AWS SQS**
- Agendamentos com **APScheduler**

---

## ☁️ Infraestrutura na Nuvem

| Serviço | Descrição |
|--------|-----------|
| EC2 | Servidor da API FastAPI |
| S3 - `telas-clientes` | Armazena os arquivos de cada cliente |
| S3 - `telas-update` | Armazena os arquivos `.zip` com updates |
| SQS | Detecta mudanças em arquivos para envio |
| Supabase | Backend alternativo e base de dados de notícias |
| Firestore | Base de dados oficial com fallback local |

---

## 🧩 Componentes do Sistema

- **📰 Widget de Notícias**
  - Fundo dinâmico com imagem do portal (quando disponível)
  - Overlay escuro com título, texto e QR Code arredondado
  - Contador de leituras de QR code

- **📢 Widget de Avisos**
  - Atualização automática com leitura de JSON
  - Substituição completa dos avisos anteriores

- **📹 Widget de Live**
  - Reprodução com `QMediaPlayer`
  - Reconexão automática quando a internet retorna
  - Detecção de travamento da live

- **🎥 Câmeras**
  - Atualização automática a cada 3 minutos

---

## 📡 Funcionamento Offline

- Cache em **SQLite** com as últimas informações válidas
- Atualização automática apenas quando houver conexão
- Redução de requisições para evitar sobrecarga

---

## 📦 Atualizações e Versionamento

- Verificação de versão a cada **20 minutos**
- Versão armazenada em JSON local
- Apenas updates incrementais são baixados
- Downgrade de versão **não permitido**

---

## 🛠️ Backend (API)

- Desenvolvido em **Python + FastAPI**
- Roda como serviço no EC2
- Integrações com Firebase, Supabase, SQS e S3
- Utiliza **APScheduler** para tarefas agendadas

---

## 📁 Gerenciamento de Arquivos

- Monitoramento de arquivos no S3 via SQS
- Geração de pacotes `.zip` com apenas arquivos novos ou deletados
- Upload direto para o S3 (sem salvar localmente)
- Histórico mantido em disco

---

## 🔐 Segurança e Estabilidade

- Controle de acesso aos buckets e API
- Comunicação segura com os serviços da AWS
- Sem necessidade de reinstalar sistema em updates

---

## 📊 Monitoramento e Logs

- Logs locais de atividade e erros
- Registro de última atualização e leitura de arquivos
- Reconhecimento de falhas de internet

---

## ⚙️ Deploy e Automação

- Script de instalação para EC2 (Ubuntu 24.04)
- Instalação automática de dependências (Python, Nginx, etc.)
- Reinício automático do sistema em falhas críticas

---

## 🧭 Roadmap Futuro

- [ ] Painel administrativo na web
- [ ] App mobile para controle remoto
- [ ] Sistema de playlists e horários por cliente
- [ ] Dashboard de análises e métricas

---

## 📄 Licença

Este projeto é privado e licenciado para uso exclusivo por [Seu Nome ou Empresa].

---

