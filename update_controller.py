def executar_atualizacoes(callback_progresso=None):
    from atualizadores import sistema, entretenimento, noticias_update

    progresso = {"total": 0, "atual": 0}

    def atualizar_barra():
        if callback_progresso and progresso["total"] > 0:
            percentual = int((progresso["atual"] / progresso["total"]) * 100)
            callback_progresso(percentual)

    def progresso_increment():
        progresso["atual"] += 1
        atualizar_barra()

    # 1️⃣ Contar arquivos pendentes
    progresso["total"] += sistema.contar_arquivos_faltando()
    progresso["total"] += entretenimento.contar_videos_faltando()
    progresso["total"] += noticias_update.contar_imagens_faltando()

    print(f"📊 Total de arquivos a baixar: {progresso['total']}")

    # 2️⃣ Executar as atualizações com callback por arquivo
    sistema.verificar_atualizacao(callback=progresso_increment)
    entretenimento.verificar_atualizacao_entretenimento(callback=progresso_increment)
    noticias_update.verificar_e_atualizar_noticias(callback=progresso_increment)

    # 3️⃣ Força o progresso para 100% no fim
    if callback_progresso:
        callback_progresso(100)
