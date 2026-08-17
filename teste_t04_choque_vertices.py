"""
T04 — Choque interno: teste da agregação entre vértices.

Reprodução da lógica observada no documento:

    M_n = (|P1_n| + |P99_n|) / 2
    M   = média simples de M_n entre os 9 vértices

Benchmark independente:

    M_DV01 = média de M_n ponderada pela sensibilidade aproximada (DV01).

Observação:
A base sintética é mensal. Por isso, 6 meses são usados como aproximação
do horizonte de 128 dias úteis da metodologia documentada.
"""

from _util import *


# ============================================================
# 1. LEITURA DOS DADOS
# ============================================================

curva = pd.read_csv(
    PASTA_DADOS / "curva_pre_sintetica.csv",
    parse_dates=["data"]
)

carteira = pd.read_csv(
    PASTA_DADOS / "carteira_sintetica.csv"
)


# ============================================================
# 2. ORGANIZAÇÃO DA CURVA
# ============================================================

painel = curva.pivot(
    index="data",
    columns="prazo_anos",
    values="taxa_pre"
).sort_index()


# ============================================================
# 3. VARIAÇÃO EM APROXIMADAMENTE 6 MESES
# ============================================================
#
# A base sintética é mensal.
# Assim, 6 observações são usadas como aproximação de
# aproximadamente 128 dias úteis.
#

variacao = painel.pct_change(6).dropna()


# ============================================================
# 4. CÁLCULO DOS PERCENTIS POR VÉRTICE
# ============================================================

linhas = []

for prazo in variacao.columns:

    p1 = variacao[prazo].quantile(0.01)
    p99 = variacao[prazo].quantile(0.99)

    # Fórmula observada no documento
    m_n = (abs(p1) + abs(p99)) / 2

    linhas.append(
        [
            prazo,
            p1,
            p99,
            m_n
        ]
    )


por_vertice = pd.DataFrame(
    linhas,
    columns=[
        "prazo_anos",
        "p1",
        "p99",
        "m_n"
    ]
)


# ============================================================
# 5. CÁLCULO DE DV01 APROXIMADO
# ============================================================
#
# DV01 não é a metodologia oficial.
#
# Ele é utilizado exclusivamente como benchmark independente
# para verificar se a média simples dos vértices pode produzir
# resultado muito diferente de uma ponderação pela exposição.
#

taxa_ref = 0.10

carteira["dv01_aprox"] = (
    carteira["nocional"].abs()
    * carteira["prazo_anos"]
    / (1 + taxa_ref) ** (carteira["prazo_anos"] + 1)
    * 1e-4
)


dv01 = (
    carteira
    .groupby(
        "prazo_anos",
        as_index=False
    )["dv01_aprox"]
    .sum()
)


# ============================================================
# 6. JUNÇÃO ENTRE CHOQUE E SENSIBILIDADE
# ============================================================

por_vertice = por_vertice.merge(
    dv01,
    on="prazo_anos",
    how="left"
)

por_vertice["dv01_aprox"] = (
    por_vertice["dv01_aprox"]
    .fillna(0)
)


# ============================================================
# 7. AGREGAÇÃO OFICIAL — MÉDIA SIMPLES
# ============================================================

m_simples = por_vertice["m_n"].mean()


# ============================================================
# 8. BENCHMARK — PONDERAÇÃO POR DV01
# ============================================================

m_dv01 = np.average(
    por_vertice["m_n"],
    weights=np.maximum(
        por_vertice["dv01_aprox"],
        1e-12
    )
)


# ============================================================
# 9. BENCHMARK ADICIONAL — MAIOR VÉRTICE
# ============================================================

m_maximo = por_vertice["m_n"].max()


# ============================================================
# 10. RESUMO
# ============================================================

resumo = pd.DataFrame(
    {
        "metodo": [
            "media_simples_documento",
            "benchmark_ponderado_dv01",
            "maximo"
        ],

        "M": [
            m_simples,
            m_dv01,
            m_maximo
        ],

        "M_pct": [
            m_simples * 100,
            m_dv01 * 100,
            m_maximo * 100
        ]
    }
)


# ============================================================
# 11. SALVAR RESULTADOS
# ============================================================

salvar_tabela(
    por_vertice,
    "t04_choque_por_vertice.csv"
)

salvar_tabela(
    resumo,
    "t04_resumo_agregacao.csv"
)


# ============================================================
# 12. FIGURA
# ============================================================

plt.figure(
    figsize=(8.5, 5)
)

plt.bar(
    [
        "Média simples\n(documento)",
        "Ponderação\npor DV01",
        "Máximo"
    ],
    resumo["M_pct"]
)

plt.ylabel("M (%)")

plt.title(
    "T04 — Agregação dos vértices"
)

salvar_figura(
    "teste_t04_choque_vertices.png"
)


# ============================================================
# 13. RESULTADO NO TERMINAL
# ============================================================

print("\nResultado T04:")
print(resumo.to_string(index=False))


# ============================================================
# 14. DIAGNÓSTICO
# ============================================================

diferenca = (
    m_simples
    - m_dv01
) * 100

print("\nDiagnóstico:")

print(
    f"Média simples = {m_simples * 100:.2f}%"
)

print(
    f"Benchmark DV01 = {m_dv01 * 100:.2f}%"
)

print(
    f"Diferença = {diferenca:.2f} p.p."
)

if m_simples < m_dv01:

    print(
        "PONTO DE ATENÇÃO: "
        "a média simples resultou em choque inferior "
        "ao benchmark ponderado por DV01."
    )

else:

    print(
        "PREMISSA NÃO REFUTADA: "
        "a média simples não apresentou diluição "
        "frente ao benchmark DV01 nesta amostra."
    )