"""
T06 — Depósitos sem vencimento: estabilidade temporal do comportamento.
"""
from _util import *

base = pd.read_csv(PASTA_DADOS/"coortes_depositos_sem_vencimento_sinteticas.csv",
                   parse_dates=["data_coorte"])

def meia_vida(g):
    g = g.sort_values("dia")
    i = (g["percentual_sobrevivencia"]-0.5).abs().idxmin()
    return g.loc[i,"dia"]

resultado = (base.groupby(["data_coorte","segmento"])
             .apply(meia_vida, include_groups=False)
             .rename("meia_vida_dias").reset_index())
salvar_tabela(resultado, "t06_meia_vida_coortes.csv")

resumo = resultado.groupby("segmento")["meia_vida_dias"].agg(
    media="mean", desvio="std", minimo="min", maximo="max"
).reset_index()
resumo["amplitude_dias"] = resumo["maximo"]-resumo["minimo"]
salvar_tabela(resumo, "t06_resumo_estabilidade.csv")

plt.figure(figsize=(10,5))
for seg,g in resultado.groupby("segmento"):
    plt.plot(g["data_coorte"], g["meia_vida_dias"], marker="o", label=seg)
plt.ylabel("Meia-vida (dias)")
plt.xlabel("Coorte")
plt.title("T06 — Estabilidade temporal dos depósitos sem vencimento")
plt.legend()
salvar_figura("teste_t06_dsv_meia_vida.png")

print(resumo.to_string(index=False))
