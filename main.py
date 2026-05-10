import os
import cv2
import numpy as np


PASTA_ENTRADA = "test"
PASTA_SAIDA = "outputs"

EXTENSOES_VALIDAS = (".png", ".jpg", ".jpeg", ".bmp", ".webp")

TOP_K = 2
AREA_MINIMA = 100


def carregar_imagens_da_pasta(pasta):
    imagens = []

    for nome_arquivo in os.listdir(pasta):
        if nome_arquivo.lower().endswith(EXTENSOES_VALIDAS):
            caminho = os.path.join(pasta, nome_arquivo)
            imagens.append(caminho)

    return imagens


def binarizar_imagem(imagem):
    cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)

    _, mascara = cv2.threshold(
        cinza,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    return mascara


def encontrar_componentes(mascara):
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        mascara,
        connectivity=8
    )

    componentes = []

    for label in range(1, num_labels):
        x = stats[label, cv2.CC_STAT_LEFT]
        y = stats[label, cv2.CC_STAT_TOP]
        largura = stats[label, cv2.CC_STAT_WIDTH]
        altura = stats[label, cv2.CC_STAT_HEIGHT]
        area = stats[label, cv2.CC_STAT_AREA]
        centro_x, centro_y = centroids[label]

        if area >= AREA_MINIMA:
            componentes.append({
                "label": label,
                "x": x,
                "y": y,
                "largura": largura,
                "altura": altura,
                "area": area,
                "centro_x": centro_x,
                "centro_y": centro_y
            })

    return componentes, labels


def merge_sort_componentes(lista):
    if len(lista) <= 1:
        return lista

    meio = len(lista) // 2

    esquerda = merge_sort_componentes(lista[:meio])
    direita = merge_sort_componentes(lista[meio:])

    return intercalar(esquerda, direita)


def intercalar(esquerda, direita):
    resultado = []
    i = 0
    j = 0

    while i < len(esquerda) and j < len(direita):
        if esquerda[i]["area"] >= direita[j]["area"]:
            resultado.append(esquerda[i])
            i += 1
        else:
            resultado.append(direita[j])
            j += 1

    while i < len(esquerda):
        resultado.append(esquerda[i])
        i += 1

    while j < len(direita):
        resultado.append(direita[j])
        j += 1

    return resultado


def gerar_resultado_visual(imagem, mascara, labels, componentes_ordenados):
    resultado = imagem.copy()
    mascara_filtrada = np.zeros_like(mascara)

    componentes_selecionados = componentes_ordenados[:TOP_K]

    for indice, componente in enumerate(componentes_selecionados, start=1):
        label = componente["label"]
        x = componente["x"]
        y = componente["y"]
        largura = componente["largura"]
        altura = componente["altura"]
        area = componente["area"]

        centro_x = int(componente["centro_x"])
        centro_y = int(componente["centro_y"])

        mascara_filtrada[labels == label] = 255

        cv2.rectangle(
            resultado,
            (x, y),
            (x + largura, y + altura),
            (0, 255, 0),
            2
        )

        cv2.circle(
            resultado,
            (centro_x, centro_y),
            5,
            (0, 0, 255),
            -1
        )

        texto = f"#{indice} area={area}"

        cv2.putText(
            resultado,
            texto,
            (x, max(y - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )

    return resultado, mascara_filtrada


def processar_imagem(caminho_imagem):
    nome_arquivo = os.path.basename(caminho_imagem)
    nome_base, _ = os.path.splitext(nome_arquivo)

    imagem = cv2.imread(caminho_imagem)

    if imagem is None:
        print(f"Erro ao carregar: {caminho_imagem}")
        return

    mascara = binarizar_imagem(imagem)

    componentes, labels = encontrar_componentes(mascara)

    componentes_ordenados = merge_sort_componentes(componentes)

    resultado, mascara_filtrada = gerar_resultado_visual(
        imagem,
        mascara,
        labels,
        componentes_ordenados
    )

    pasta_imagem_saida = os.path.join(PASTA_SAIDA, nome_base)
    os.makedirs(pasta_imagem_saida, exist_ok=True)

    caminho_mascara = os.path.join(pasta_imagem_saida, "01_mascara_binaria.png")
    caminho_filtrada = os.path.join(pasta_imagem_saida, "02_componentes_selecionados.png")
    caminho_resultado = os.path.join(pasta_imagem_saida, "03_resultado_ordenado.png")

    cv2.imwrite(caminho_mascara, mascara)
    cv2.imwrite(caminho_filtrada, mascara_filtrada)
    cv2.imwrite(caminho_resultado, resultado)

    print(f"\nImagem processada: {nome_arquivo}")
    print(f"Componentes encontrados: {len(componentes_ordenados)}")
    print(f"Resultado salvo em: {caminho_resultado}")


def main():
    if not os.path.exists(PASTA_ENTRADA):
        print(f"Erro: a pasta '{PASTA_ENTRADA}' nao existe.")
        return

    os.makedirs(PASTA_SAIDA, exist_ok=True)

    imagens = carregar_imagens_da_pasta(PASTA_ENTRADA)

    if len(imagens) == 0:
        print(f"Nenhuma imagem encontrada na pasta '{PASTA_ENTRADA}'.")
        return

    for caminho_imagem in imagens:
        processar_imagem(caminho_imagem)

    print("\nProcessamento finalizado.")
    print(f"Resultados salvos na pasta: {PASTA_SAIDA}")


if __name__ == "__main__":
    main()