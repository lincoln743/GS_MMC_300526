# -*- coding: utf-8 -*-
"""
gerar_graficos.py
Gera todas as figuras do relatorio a partir de ../dados/cena.npz.
Cada figura ilustra uma etapa da modelagem por transformacoes lineares.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrow
from scipy import ndimage
import os

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
})
OUT = "../imagens"
os.makedirs(OUT, exist_ok=True)

d = np.load("../dados/cena.npz")
t1, t2 = d["t1"], d["t2"]
rio, novo_desmate = d["rio"], d["novo_desmate"]
N = t1.shape[0]

# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def rgb_stretch(img):
    """Composicao cor verdadeira (R,G,B) com realce percentil para exibicao."""
    r, g, b = img[..., 2], img[..., 1], img[..., 0]
    comp = np.dstack([r, g, b])
    lo, hi = np.percentile(comp, 2), np.percentile(comp, 98)
    return np.clip((comp - lo) / (hi - lo + 1e-9), 0, 1)

# Matriz da transformacao espectral linear (tipo "Tasseled Cap" didatica)
# Linhas: Brilho, Verdor, Umidade ; Colunas (bandas): [B, G, R, NIR]
M = np.array([
    [ 0.33,  0.34,  0.33,  0.49],   # Brilho
    [-0.27, -0.22, -0.55,  0.72],   # Verdor
    [ 0.19,  0.31,  0.24, -0.61],   # Umidade
])

def aplica_M(img):
    P = img.reshape(-1, 4)          # (N*N, 4)
    Y = P @ M.T                     # (N*N, 3)
    return Y.reshape(N, N, 3)

# ===========================================================================
# FIGURA 1 - Composicao RGB das duas datas
# ===========================================================================
fig, ax = plt.subplots(1, 2, figsize=(9, 4.6))
ax[0].imshow(rgb_stretch(t1)); ax[0].set_title("(a) Cena $t_1$ — 2019")
ax[1].imshow(rgb_stretch(t2)); ax[1].set_title("(b) Cena $t_2$ — 2024")
for a in ax:
    a.set_xlabel("coluna $j$ (pixel)"); a.set_ylabel("linha $i$ (pixel)")
fig.suptitle("Imagem de satélite como matriz: composição cor-verdadeira (R,G,B)",
             fontsize=12, fontweight="bold")
fig.tight_layout()
fig.savefig(f"{OUT}/fig01_cena_rgb.png"); plt.close(fig)
print("fig01 ok")

# ===========================================================================
# FIGURA 2 - Transformacao linear no plano: vetores-base -> paralelogramo
# A = R(theta) . S   (rotacao composta com escala)
# ===========================================================================
theta = np.deg2rad(25)
S = np.array([[1.6, 0.0], [0.0, 0.9]])
R = np.array([[np.cos(theta), -np.sin(theta)],
              [np.sin(theta),  np.cos(theta)]])
A = R @ S
detA = np.linalg.det(A)
e1, e2 = np.array([1, 0]), np.array([0, 1])
Ae1, Ae2 = A @ e1, A @ e2

fig, ax = plt.subplots(1, 2, figsize=(9, 4.4))
# painel esquerdo: base canonica + quadrado unitario
sq = np.array([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]])
ax[0].plot(sq[:, 0], sq[:, 1], color="#1f77b4")
ax[0].fill(sq[:, 0], sq[:, 1], color="#1f77b4", alpha=0.15)
ax[0].annotate("", (1, 0), (0, 0), arrowprops=dict(arrowstyle="->", color="#d62728", lw=2))
ax[0].annotate("", (0, 1), (0, 0), arrowprops=dict(arrowstyle="->", color="#2ca02c", lw=2))
ax[0].text(1.02, -0.12, r"$e_1$", color="#d62728")
ax[0].text(-0.18, 1.02, r"$e_2$", color="#2ca02c")
ax[0].set_title("(a) Espaço de entrada\nárea = 1")
# painel direito: imagem da base + paralelogramo
par = np.array([[0, 0], Ae1, Ae1 + Ae2, Ae2, [0, 0]])
ax[1].plot(par[:, 0], par[:, 1], color="#ff7f0e")
ax[1].fill(par[:, 0], par[:, 1], color="#ff7f0e", alpha=0.18)
ax[1].annotate("", Ae1, (0, 0), arrowprops=dict(arrowstyle="->", color="#d62728", lw=2))
ax[1].annotate("", Ae2, (0, 0), arrowprops=dict(arrowstyle="->", color="#2ca02c", lw=2))
ax[1].text(Ae1[0]+0.03, Ae1[1]-0.12, r"$Ae_1$", color="#d62728")
ax[1].text(Ae2[0]-0.35, Ae2[1]+0.05, r"$Ae_2$", color="#2ca02c")
ax[1].set_title(f"(b) Após $A=R(\\theta)\\,S$\nárea = |det A| = {abs(detA):.2f}")
for a in ax:
    a.set_aspect("equal"); a.grid(alpha=0.3)
    a.set_xlim(-0.6, 2.0); a.set_ylim(-0.6, 2.0)
    a.axhline(0, color="k", lw=0.5); a.axvline(0, color="k", lw=0.5)
fig.suptitle("Interpretação geométrica de uma transformação linear no plano",
             fontsize=12, fontweight="bold")
fig.tight_layout()
fig.savefig(f"{OUT}/fig02_algebra_vetores.png"); plt.close(fig)
print("fig02 ok  det(A) =", round(detA, 3))

# ===========================================================================
# FIGURA 3 - Registro de imagens (transformacao geometrica afim)
# Simula aquisicao desalinhada de t2 e a re-registra pela transformacao inversa
# ===========================================================================
rgb2 = rgb_stretch(t2)
ang = np.deg2rad(12)
Sc = np.array([[1.12, 0.0], [0.0, 0.92]])
Rg = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]])
W = Rg @ Sc                      # transformacao de desalinhamento
c = np.array([N/2, N/2])

def warp(rgb, mat):
    out = np.zeros_like(rgb)
    inv = np.linalg.inv(mat)
    off = c - inv @ c
    for k in range(3):
        out[..., k] = ndimage.affine_transform(
            rgb[..., k], inv, offset=off, order=1, mode="constant", cval=0.0)
    return out

desalinhada = warp(rgb2, W)          # imagem "como adquirida"
registrada = warp(desalinhada, np.linalg.inv(W))  # aplica inversa -> alinha

fig, ax = plt.subplots(1, 3, figsize=(11.5, 4.2))
ax[0].imshow(rgb2);        ax[0].set_title("(a) Referência $t_1$")
ax[1].imshow(desalinhada); ax[1].set_title("(b) Aquisição desalinhada\n($W=R\\,S$ aplicada)")
ax[2].imshow(registrada);  ax[2].set_title("(c) Registrada ($W^{-1}$)")
for a in ax:
    a.set_xticks([]); a.set_yticks([])
fig.suptitle("Registro de imagens por transformação geométrica (afim)",
             fontsize=12, fontweight="bold", y=1.04)
fig.tight_layout(rect=[0, 0, 1, 0.98])
fig.savefig(f"{OUT}/fig03_transformacao_geometrica.png"); plt.close(fig)
print("fig03 ok")

# ===========================================================================
# FIGURA 4 - Transformacao espectral linear  y = M p
# ===========================================================================
Y = aplica_M(t2)
titulos = ["Brilho (B)", "Verdor (G)", "Umidade (W)"]
cmaps = ["gray", "RdYlGn", "Blues"]
fig, ax = plt.subplots(1, 4, figsize=(13.5, 3.8))
ax[0].imshow(rgb_stretch(t2)); ax[0].set_title("Entrada (R,G,B)")
ax[0].set_xticks([]); ax[0].set_yticks([])
for k in range(3):
    im = ax[k+1].imshow(Y[..., k], cmap=cmaps[k])
    ax[k+1].set_title(titulos[k]); ax[k+1].set_xticks([]); ax[k+1].set_yticks([])
    fig.colorbar(im, ax=ax[k+1], fraction=0.046, pad=0.04)
fig.suptitle(r"Transformação espectral linear $y = M\,p$ : separação de componentes",
             fontsize=12, fontweight="bold")
fig.tight_layout()
fig.savefig(f"{OUT}/fig04_transformacao_espectral.png"); plt.close(fig)
print("fig04 ok")

# ===========================================================================
# FIGURA 5 - Realce linear de contraste  g(x) = alpha*x + beta
# ===========================================================================
verdor = aplica_M(t2)[..., 1]
v = verdor.copy()
p2, p98 = np.percentile(v, 2), np.percentile(v, 98)
alpha = 1.0 / (p98 - p2)
beta = -p2 * alpha
v_realc = np.clip(alpha * v + beta, 0, 1)

fig, ax = plt.subplots(2, 2, figsize=(9.5, 7.2))
im0 = ax[0, 0].imshow(v, cmap="RdYlGn"); ax[0, 0].set_title("(a) Verdor original")
fig.colorbar(im0, ax=ax[0, 0], fraction=0.046, pad=0.04)
im1 = ax[0, 1].imshow(v_realc, cmap="RdYlGn"); ax[0, 1].set_title("(b) Verdor realçado")
fig.colorbar(im1, ax=ax[0, 1], fraction=0.046, pad=0.04)
for a in (ax[0, 0], ax[0, 1]):
    a.set_xticks([]); a.set_yticks([])
ax[1, 0].hist(v.ravel(), bins=60, color="#6699cc"); ax[1, 0].set_title("(c) Histograma original")
ax[1, 1].hist(v_realc.ravel(), bins=60, color="#cc8866"); ax[1, 1].set_title("(d) Histograma realçado")
for a in (ax[1, 0], ax[1, 1]):
    a.set_xlabel("intensidade"); a.set_ylabel("frequência")
fig.suptitle(r"Realce linear de contraste: $g(x)=\alpha x+\beta$"
             f"   ($\\alpha={alpha:.2f},\\ \\beta={beta:.2f}$)",
             fontsize=12, fontweight="bold")
fig.tight_layout()
fig.savefig(f"{OUT}/fig05_realce_contraste.png"); plt.close(fig)
print("fig05 ok  alpha =", round(alpha, 3), "beta =", round(beta, 3))

# ===========================================================================
# FIGURA 6 - Deteccao de mudanca (desmatamento) entre t1 e t2
# ===========================================================================
g1 = aplica_M(t1)[..., 1]
g2 = aplica_M(t2)[..., 1]
diff = g2 - g1
limiar = -0.05
perda = diff < limiar
perda[rio] = False
area_total = N * N
area_perda = perda.sum()
pct = 100.0 * area_perda / area_total

fig, ax = plt.subplots(1, 3, figsize=(12.5, 4.3))
im0 = ax[0].imshow(g1, cmap="RdYlGn", vmin=-0.1, vmax=0.35); ax[0].set_title("(a) Verdor $t_1$ (2019)")
im1 = ax[1].imshow(g2, cmap="RdYlGn", vmin=-0.1, vmax=0.35); ax[1].set_title("(b) Verdor $t_2$ (2024)")
ax[2].imshow(g2, cmap="gray")
mask = np.ma.masked_where(~perda, perda)
ax[2].imshow(mask, cmap="autumn", alpha=0.9)
ax[2].set_title(f"(c) Perda detectada\n$\\Delta<{limiar}$  →  {pct:.1f}% da área")
for a, im in zip(ax[:2], [im0, im1]):
    fig.colorbar(im, ax=a, fraction=0.046, pad=0.04)
for a in ax:
    a.set_xticks([]); a.set_yticks([])
fig.suptitle(r"Detecção de mudança por subtração matricial: $\Delta = G(t_2)-G(t_1)$",
             fontsize=12, fontweight="bold")
fig.tight_layout()
fig.savefig(f"{OUT}/fig06_deteccao_mudanca.png"); plt.close(fig)
print(f"fig06 ok  perda = {area_perda} px = {pct:.2f}%")

# salva metricas para uso no relatorio
with open("../dados/metricas.txt", "w", encoding="utf-8") as f:
    f.write(f"det_A={detA:.4f}\n")
    f.write(f"alpha={alpha:.4f}\nbeta={beta:.4f}\n")
    f.write(f"area_total_px={area_total}\narea_perda_px={int(area_perda)}\npct_perda={pct:.2f}\n")
print("\nTodas as figuras geradas com sucesso.")
