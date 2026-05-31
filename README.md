# GS — Modelagem Matemática e Computacional
## Modelagem de imagens de satélite por transformações lineares: monitoramento do desmatamento

**Tema do semestre:** Indústria Espacial
**Disciplina:** Modelagem Matemática e Computacional
**Professor:** Igor Gimenes Cesca

**Integrantes:**
- Lincoln Simão Pereira — RM 567284
- Miguel Silva Bezerra — RM 566763
- Nicolas Sakaue Nishimura — RM 567752

---

## Descrição

O projeto modela imagens multiespectrais de satélite como matrizes e aplica
**transformações lineares** da Álgebra Linear para monitorar o avanço do
desmatamento em uma área florestal, comparando duas datas (2019 e 2024).

Transformações implementadas:
1. **Espectral** — `y = M·p` (matriz 3×4 tipo *Tasseled Cap*): separa Brilho, Verdor e Umidade.
2. **Geométrica afim** — `W = R(θ)·S` e sua inversa `W⁻¹` para registro (alinhamento) de imagens.
3. **Realce de contraste** — `g(x) = α·x + β`.
4. **Detecção de mudança** — subtração matricial `Δ = G(t₂) − G(t₁)`.

Resultado: perda de cobertura vegetal de ~13,3% da área (~64,5 ha).

---

## Estrutura

```
GS_MMC/
├── README.md
├── codigo/
│   ├── gerar_dados.py        # gera a base sintetica (rasters + CSV)
│   └── gerar_graficos.py     # gera as 6 figuras do relatorio
├── dados/
│   ├── cena.npz              # rasters multiespectrais t1 e t2
│   ├── dados_satelite.csv    # tabela agregada (25 setores x 2 datas)
│   └── metricas.txt          # metricas calculadas (det, alpha, beta, % perda)
├── imagens/
│   └── fig01..fig06 .png      # figuras geradas
└── relatorio/
    ├── relatorio.tex          # fonte LaTeX (padrao ABNT)
    └── relatorio.pdf          # documento final (11 paginas)
```

---

## Como reproduzir

Requisitos: Python 3 (numpy, matplotlib, scipy) e LaTeX (pdflatex + babel/xurl).

```bash
# 1) gerar a base de dados
cd codigo
python3 gerar_dados.py

# 2) gerar as figuras
python3 gerar_graficos.py

# 3) compilar o relatorio (duas passadas para o sumario)
cd ../relatorio
pdflatex -interaction=nonstopmode relatorio.tex
pdflatex -interaction=nonstopmode relatorio.tex
```
