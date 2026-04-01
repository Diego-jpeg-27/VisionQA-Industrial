import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage
from services.processor import processar_imagem
from repository.database import salvar_imagem, salvar_fatia, salvar_inspecao

# constantes de detecção
LIMIAR_PIXEL = 25.0          # sensibilidade de diferença por pixel
TAMANHO_MINIMO_DEFEITO = 50  # mínimo de pixels contíguos para ser defeito real
RESULTADO_FOLDER = "/tmp/visionqa/resultados"

# garante que a pasta existe
os.makedirs(RESULTADO_FOLDER, exist_ok=True)  


def pre_processar(caminho):
    """abre imagem, aplica desfoque leve e retorna array numpy"""
    img = Image.open(caminho).convert("RGB")
    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    return np.array(img, dtype=np.float32)


def comparar_fatias(fatias_ref, fatias_teste):
    """calcula diferença por fatia e retorna as que ultrapassam o limiar"""
    fatias_com_defeito = []
    for thread_id in fatias_ref:
        ref = fatias_ref[thread_id]
        teste = fatias_teste[thread_id]
        diferenca = np.sqrt(
            (ref["media_r"] - teste["media_r"]) ** 2 +
            (ref["media_g"] - teste["media_g"]) ** 2 +
            (ref["media_b"] - teste["media_b"]) ** 2
        )
        if diferenca > LIMIAR_PIXEL:
            fatias_com_defeito.append({**teste, "diferenca": diferenca})
    percentual = (len(fatias_com_defeito) / len(fatias_ref)) * 100
    return fatias_com_defeito, percentual


def detectar_regioes_defeituosas(caminho_ref, caminho_teste):
    """
    compara pixel a pixel, agrupa regiões contíguas e filtra ruído
    retorna lista de defeitos, mapa binário, percentual e dimensões
    """
    # carrega e pré-processa as imagens
    img_ref = pre_processar(caminho_ref)
    img_teste = pre_processar(caminho_teste)

    # ajusta para o menor tamanho comum
    h = min(img_ref.shape[0], img_teste.shape[0])
    w = min(img_ref.shape[1], img_teste.shape[1])
    img_ref = img_ref[:h, :w]
    img_teste = img_teste[:h, :w]

    # mapa de diferença por pixel
    diferenca = np.sqrt(np.sum((img_ref - img_teste) ** 2, axis=2))
    mapa_bruto = diferenca > LIMIAR_PIXEL

    # agrupa pixels vizinhos em regiões (conectividade 8)
    estrutura = ndimage.generate_binary_structure(2, 2)
    regioes_rotuladas, num_regioes = ndimage.label(mapa_bruto, structure=estrutura)

    defeitos = []
    mapa_final = np.zeros_like(mapa_bruto, dtype=bool)

    for regiao_id in range(1, num_regioes + 1):
        mascara = regioes_rotuladas == regiao_id
        tamanho = np.sum(mascara)

        # descarta regiões muito pequenas (ruído)
        if tamanho < TAMANHO_MINIMO_DEFEITO:
            continue

        # bounding box da região
        posicoes = np.argwhere(mascara)
        y_min, x_min = posicoes.min(axis=0)
        y_max, x_max = posicoes.max(axis=0)

        # severidade = média das diferenças na região
        severidade = float(np.mean(diferenca[mascara]))

        defeitos.append({
            "x_min": int(x_min),
            "y_min": int(y_min),
            "x_max": int(x_max),
            "y_max": int(y_max),
            "tamanho": int(tamanho),
            "severidade": round(severidade, 2)
        })

        mapa_final[mascara] = True

    total_pixels = h * w
    pixels_defeituosos = int(np.sum(mapa_final))
    percentual = round((pixels_defeituosos / total_pixels) * 100, 4)

    return defeitos, mapa_final, percentual, (h, w)


def gerar_imagem_resultado(caminho_teste, defeitos, dimensoes):
    """desenha retângulos vermelhos e etiquetas nos defeitos"""
    img = Image.open(caminho_teste).convert("RGB")
    draw = ImageDraw.Draw(img)

    for i, defeito in enumerate(defeitos):
        x_min = defeito["x_min"]
        y_min = defeito["y_min"]
        x_max = defeito["x_max"]
        y_max = defeito["y_max"]

        # contorno vermelho
        draw.rectangle([x_min, y_min, x_max, y_max], outline="red", width=3)

        # etiqueta com número e severidade
        label = f"#{i+1} sev:{defeito['severidade']:.0f}"
        draw.rectangle([x_min, y_min - 16, x_min + len(label) * 7, y_min], fill="red")
        draw.text((x_min + 2, y_min - 15), label, fill="white")

    return img


def inspecionar(caminho_ref, caminho_teste, nome_ref, nome_teste):
    """executa inspeção completa: salva dados no banco e retorna resultado"""
   
    # processa imagens em fatias (via processor)
    imagem_ref, largura, altura, fatias_ref = processar_imagem(caminho_ref)
    imagem_teste, _, _, fatias_teste = processar_imagem(caminho_teste)

    # salva metadados das imagens no banco
    ref_id = salvar_imagem(nome_ref, largura, altura, "referencia")
    teste_id = salvar_imagem(nome_teste, largura, altura, "teste")

    # salva todas as fatias no banco
    for thread_id, fatia in fatias_ref.items():
        salvar_fatia(ref_id, fatia["thread_id"], fatia["y_inicio"],
                     fatia["y_fim"], fatia["media_r"], fatia["media_g"], fatia["media_b"])

    for thread_id, fatia in fatias_teste.items():
        salvar_fatia(teste_id, fatia["thread_id"], fatia["y_inicio"],
                     fatia["y_fim"], fatia["media_r"], fatia["media_g"], fatia["media_b"])

    # detecção precisa de defeitos (regiões muito proximas)
    defeitos, mapa_final, percentual, dimensoes = detectar_regioes_defeituosas(
        caminho_ref, caminho_teste
    )

    status = "REPROVADO" if len(defeitos) > 0 else "APROVADO"

    # gera imagem com anotações
    imagem_resultado = gerar_imagem_resultado(caminho_teste, defeitos, dimensoes)
    nome_resultado = f"resultado_{ref_id}_{teste_id}.jpg"
    caminho_resultado = os.path.join(RESULTADO_FOLDER, nome_resultado)
    imagem_resultado.save(caminho_resultado, format="JPEG")

    # salva registro da inspeção
    inspecao_id = salvar_inspecao(ref_id, teste_id, percentual, status, nome_resultado)

    return {
        "inspecao_id": inspecao_id,
        "percentual_defeito": percentual,
        "status": status,
        "fatias_com_defeito": len(defeitos),
        "imagem_resultado": imagem_resultado
    }