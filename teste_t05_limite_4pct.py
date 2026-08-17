"""
T05 — Choque interno: efeito do limite de 4%.

Reprodução da lógica observada no documento:

    M_n = (|P1_n| + |P99_n|) / 2

    M = média dos M_n

    MC = média dos níveis da curva no último ano

    R_p_sem_limite = MC * M

    R_p = min(4%, R_p_sem_limite)

Objetivo da validação:

Verificar se o limite de 4% é acionado com frequência
e se reduz materialmente a severidade calculada.
"""

from _util import *


# ============================================================
# 1. LEITURA DA CURVA
# ============================================================

curva = pd.read_csv(
    PASTA_DADOS / "curva_pre_sintetica.csv",
    parse_dates=["data"]
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
# 3. PARÂMETROS DO TESTE
# ============================================================
#
# O documento utiliza histórico longo.
#
# Como a base sintética é mensal:
#
# 16 anos × 12 meses = 192 observações
#
# E utilizamos 6 meses como aproximação de
# aproximadamente 128 dias úteis.
#

janela_historica = 16 * 12

horizonte_meses = 6


# ============================================================
# 4. RECALIBRAÇÃO AO LONGO DO TEMPO
# ============================================================

linhas = []


for i in range(
    janela_historica,
    len(painel)
):

    # --------------------------------------------------------
    # Histórico disponível naquela data
    # --------------------------------------------------------

    hist = painel.iloc[
        i - janela_historica:i
    ]


    # --------------------------------------------------------
    # Variações em aproximadamente 6 meses
    # --------------------------------------------------------

    variacao = (
        hist
        .pct_change(horizonte_meses)
        .dropna()
    )


    # --------------------------------------------------------
    # Cálculo de M_n
    # --------------------------------------------------------

    m_ns = []


    for prazo in variacao.columns:

        p1 = (
            variacao[prazo]
            .quantile(0.01)
        )

        p99 = (
            variacao[prazo]
            .quantile(0.99)
        )


        m_n = (
            abs(p1)
            +
            abs(p99)
        ) / 2


        m_ns.append(
            m_n
        )


    # --------------------------------------------------------
    # Média entre vértices
    # --------------------------------------------------------

    M = float(
        np.mean(m_ns)
    )


    # --------------------------------------------------------
    # MC
    #
    # Média dos níveis da curva no último ano
    # --------------------------------------------------------

    MC = float(
        hist
        .tail(12)
        .mean()
        .mean()
    )


    # --------------------------------------------------------
    # R_p ANTES DO LIMITE
    # --------------------------------------------------------

    rp_sem_limite = (
        MC * M
    )


    # --------------------------------------------------------
    # R_p DEPOIS DO LIMITE
    # --------------------------------------------------------

    rp_com_limite = min(
        0.04,
        rp_sem_limite
    )


    # --------------------------------------------------------
    # Guarda resultado
    # --------------------------------------------------------

    linhas.append(
        [
            painel.index[i],
            M,
            MC,
            rp_sem_limite,
            rp_com_limite,
            rp_sem_limite > 0.04
        ]
    )


# ============================================================
# 5. DATAFRAME DOS RESULTADOS
# ============================================================

resultado = pd.DataFrame(
    linhas,
    columns=[
        "data",
        "M",
        "MC",
        "rp_sem_limite",
        "rp_com_limite",
        "limite_ativo"
    ]
)


# ============================================================
# 6. REDUÇÃO CAUSADA PELO LIMITE
# ============================================================

resultado["reducao_relativa"] = np.where(

    resultado["rp_sem_limite"] > 0,

    1
    -
    (
        resultado["rp_com_limite"]
        /
        resultado["rp_sem_limite"]
    ),

    0
)


# ============================================================
# 7. SALVAR SÉRIE COMPLETA
# ============================================================

salvar_tabela(
    resultado,
    "t05_limite_4pct.csv"
)


# ============================================================
# 8. RESUMO DO TESTE
# ============================================================

resumo = pd.DataFrame(
    [
        {

            "media_sem_limite":
                resultado[
                    "rp_sem_limite"
                ].mean(),

            "media_com_limite":
                resultado[
                    "rp_com_limite"
                ].mean(),

            "frequencia_limite_pct":
                resultado[
                    "limite_ativo"
                ].mean()
                * 100,

            "reducao_media_pct":
                resultado[
                    "reducao_relativa"
                ].mean()
                * 100,

            "n_observacoes":
                len(resultado)

        }
    ]
)


salvar_tabela(
    resumo,
    "t05_resumo_limite_4pct.csv"
)


# ============================================================
# 9. FIGURA
# ============================================================

plt.figure(
    figsize=(9.5, 5)
)


plt.plot(
    resultado["data"],
    resultado["rp_sem_limite"] * 100,
    marker="o",
    label="Sem limite"
)


plt.plot(
    resultado["data"],
    resultado["rp_com_limite"] * 100,
    marker="o",
    label="Com limite"
)


plt.axhline(
    4,
    linestyle="--",
    label="Limite de 4%"
)


plt.ylabel(
    "Rₚ (%)"
)


plt.title(
    "T05 — Efeito do limite de 4%"
)


plt.legend()


salvar_figura(
    "teste_t05_limite_4pct.png"
)


# ============================================================
# 10. RESULTADO NO TERMINAL
# ============================================================

print("\nResultado T05:")
print(
    resumo.to_string(
        index=False
    )
)


# ============================================================
# 11. CONCLUSÃO AUTOMÁTICA
# ============================================================

frequencia = float(
    resumo[
        "frequencia_limite_pct"
    ].iloc[0]
)


reducao = float(
    resumo[
        "reducao_media_pct"
    ].iloc[0]
)


n = int(
    resumo[
        "n_observacoes"
    ].iloc[0]
)


print("\nDiagnóstico:")

print(
    f"Número de observações = {n}"
)

print(
    f"Frequência de ativação = {frequencia:.2f}%"
)

print(
    f"Redução média = {reducao:.2f}%"
)


if (
    frequencia > 20
    and
    reducao > 5
):

    print(
        "PONTO DE ATENÇÃO: "
        "o limite atua frequentemente e produz "
        "redução relevante do choque."
    )

else:

    print(
        "SEM EVIDÊNCIA FORTE DE MATERIALIDADE: "
        "o laboratório não demonstrou redução "
        "sistematicamente relevante causada pelo limite."
    )