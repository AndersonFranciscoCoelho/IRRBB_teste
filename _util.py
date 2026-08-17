from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

RAIZ = Path(__file__).resolve().parent.parent
PASTA_DADOS = RAIZ / "dados"
PASTA_FIGURAS = RAIZ / "figuras"
PASTA_RESULTADOS = RAIZ / "resultados"

PASTA_FIGURAS.mkdir(parents=True, exist_ok=True)
PASTA_RESULTADOS.mkdir(parents=True, exist_ok=True)

def salvar_tabela(df, nome):
    caminho = PASTA_RESULTADOS / nome
    df.to_csv(caminho, index=False)
    print(f"Tabela salva: {caminho}")
    return caminho

def salvar_figura(nome):
    caminho = PASTA_FIGURAS / nome
    plt.tight_layout()
    plt.savefig(caminho, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Figura salva: {caminho}")
    return caminho

def cpr_anualizada(tam):
    return (1 + tam) ** 12 - 1
