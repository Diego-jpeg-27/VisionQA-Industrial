import threading
from PIL import Image

def processar_fatia(imagem, y_inicio, y_fim, thread_id, resultados):
    """
    processa uma fatia horizontal da imagem
    calcula a média rgb de todos os pixels da fatia
    """
    largura = imagem.width
    total_r, total_g, total_b = 0, 0, 0
    total_pixels = 0

    # percorre todos os pixels da fatia
    for y in range(y_inicio, y_fim):
        for x in range(largura):
            r, g, b = imagem.getpixel((x, y))
            total_r += r
            total_g += g
            total_b += b
            total_pixels += 1

    # calcula as médias
    media_r = total_r / total_pixels
    media_g = total_g / total_pixels
    media_b = total_b / total_pixels

    # armazena o resultado no dicionário compartilhado
    resultados[thread_id] = {
        "thread_id": thread_id,
        "y_inicio": y_inicio,
        "y_fim": y_fim,
        "media_r": media_r,
        "media_g": media_g,
        "media_b": media_b
    }

def processar_imagem(caminho, num_threads=4):
    """
    divide a imagem em fatias e processa cada uma em uma thread separada
    retorna os dados de cada fatia processada
    """
    imagem = Image.open(caminho).convert("RGB")
    largura, altura = imagem.size
    altura_fatia = altura // num_threads

    resultados = {}
    threads = []

    # cria e inicia uma thread para cada fatia
    for i in range(num_threads):
        y_inicio = i * altura_fatia
        y_fim = (i + 1) * altura_fatia if i != num_threads - 1 else altura
        t = threading.Thread(
            target=processar_fatia,
            args=(imagem, y_inicio, y_fim, i, resultados)
        )
        threads.append(t)
        t.start()

    # aguarda todas as threads terminarem
    for t in threads:
        t.join()

    return imagem, largura, altura, resultados