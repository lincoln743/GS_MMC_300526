# -*- coding: utf-8 -*-
"""
gerar_dados.py
Gera uma base de dados sintetica, porem verossimil, de imagens multiespectrais
de satelite para duas datas distintas (t1 e t2) sobre uma mesma area de floresta.

Cada imagem e' modelada como uma matriz; cada pixel possui 4 bandas espectrais:
  - B (azul), G (verde), R (vermelho), NIR (infravermelho proximo)
Valores em reflectancia [0,1], coerentes com assinaturas espectrais reais de
vegetacao, solo exposto e agua.

Saidas:
  ../dados/cena.npz          -> rasters (B,G,R,NIR) de t1 e t2 + mascaras
  ../dados/dados_satelite.csv -> tabela agregada por setor (talhao) e por data
"""
import numpy as np
import csv
import os

np.random.seed(42)

N = 220                      # imagem N x N pixels
os.makedirs("../dados", exist_ok=True)

# ----------------------------------------------------------------------------
# Assinaturas espectrais medias (reflectancia) por classe de cobertura do solo
# ordem das bandas: [Azul, Verde, Vermelho, NIR]
# ----------------------------------------------------------------------------
ASS = {
    "floresta": np.array([0.04, 0.09, 0.05, 0.46]),   # vegetacao sadia: NIR alto
    "solo":     np.array([0.13, 0.19, 0.26, 0.30]),   # solo exposto: R > G, NIR medio
    "agua":     np.array([0.05, 0.06, 0.04, 0.02]),   # corpo d'agua: tudo baixo
}

def cena_vazia():
    return np.zeros((N, N, 4), dtype=np.float32)

def preenche(img, mascara, classe, ruido=0.02):
    """Aplica a assinatura espectral de uma classe nos pixels da mascara."""
    base = ASS[classe]
    for b in range(4):
        img[..., b] = np.where(
            mascara,
            base[b] + np.random.normal(0, ruido, size=(N, N)),
            img[..., b],
        )

def disco(cx, cy, raio):
    yy, xx = np.mgrid[0:N, 0:N]
    return (xx - cx) ** 2 + (yy - cy) ** 2 <= raio ** 2

def retangulo(x0, y0, x1, y1):
    yy, xx = np.mgrid[0:N, 0:N]
    return (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)

# ----------------------------------------------------------------------------
# DATA t1 (referencia): floresta quase intacta + um rio diagonal
# ----------------------------------------------------------------------------
t1 = cena_vazia()
preenche(t1, np.ones((N, N), bool), "floresta")          # tudo floresta

# rio (faixa diagonal) - corpo d'agua
yy, xx = np.mgrid[0:N, 0:N]
rio = np.abs((yy - 0.6 * xx) - 30) < 7
preenche(t1, rio, "agua", ruido=0.01)

# pequeno desmatamento pre-existente em t1
desmate_t1 = disco(60, 150, 16) | retangulo(150, 30, 175, 55)
preenche(t1, desmate_t1 & ~rio, "solo")

# ----------------------------------------------------------------------------
# DATA t2 (atual): mesma area, mas com avanco do desmatamento
# ----------------------------------------------------------------------------
t2 = t1.copy()
# novos poligonos de desmatamento (espinha de peixe + grandes clareiras)
novos = (
    disco(60, 150, 28) |                 # clareira antiga expandida
    retangulo(150, 30, 195, 70) |        # area de pasto expandida
    disco(120, 120, 30) |                # nova grande clareira central
    retangulo(30, 90, 110, 102) |        # estrada/ramal (espinha de peixe)
    retangulo(64, 90, 76, 160) |         # ramal perpendicular 1
    retangulo(95, 60, 107, 130)          # ramal perpendicular 2
)
preenche(t2, novos & ~rio, "solo")

# garante faixa [0,1]
t1 = np.clip(t1, 0, 1)
t2 = np.clip(t2, 0, 1)

# mascara de desmatamento "verdade de campo" (para validar resultados depois)
solo_t1 = desmate_t1 & ~rio
solo_t2 = (desmate_t1 | novos) & ~rio
novo_desmate = solo_t2 & ~solo_t1

np.savez_compressed(
    "../dados/cena.npz",
    t1=t1, t2=t2, rio=rio,
    solo_t1=solo_t1, solo_t2=solo_t2, novo_desmate=novo_desmate,
)
print("Rasters salvos em ../dados/cena.npz  shape =", t1.shape)

# ----------------------------------------------------------------------------
# Tabela agregada por SETOR (talhao). Grade 5x5 = 25 setores.
# Para cada setor e cada data: media das 4 bandas e indice de verdor (greenness)
# Greenness e' a 2a componente da transformacao espectral linear M (ver relatorio)
# ----------------------------------------------------------------------------
# vetor de coeficientes da componente "Verdor" (greenness) da matriz M
g_coef = np.array([-0.27, -0.22, -0.55, 0.72])   # [B,G,R,NIR]

def greenness(pix4):  # pix4: (...,4)
    return pix4 @ g_coef

K = 5
passo = N // K
linhas = []
for i in range(K):
    for j in range(K):
        y0, y1 = i * passo, (i + 1) * passo
        x0, x1 = j * passo, (j + 1) * passo
        setor = f"S{i*K + j + 1:02d}"
        for data, img in (("2019", t1), ("2024", t2)):
            bloco = img[y0:y1, x0:x1, :]
            mb = bloco.reshape(-1, 4).mean(axis=0)
            g = float(greenness(mb))
            classe = "Floresta" if g > 0.18 else "Desmatado"
            linhas.append({
                "setor": setor, "ano": data,
                "B": round(float(mb[0]), 3), "G": round(float(mb[1]), 3),
                "R": round(float(mb[2]), 3), "NIR": round(float(mb[3]), 3),
                "verdor": round(g, 3), "classe": classe,
            })

with open("../dados/dados_satelite.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["setor", "ano", "B", "G", "R", "NIR", "verdor", "classe"])
    w.writeheader()
    w.writerows(linhas)

print(f"Tabela salva em ../dados/dados_satelite.csv  ({len(linhas)} linhas)")
