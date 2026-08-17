"""
T02 — CPR: adequação da granularidade de segmentação.
Premissa desafiada: produto como agrupamento suficiente para comportamento de antecipação.
"""
from _util import *

base = pd.read_csv(PASTA_DADOS/"historico_cpr_sintetico.csv", parse_dates=["data"])
corte = base["data"].max() - pd.DateOffset(months=12)
recente = base[base["data"] >= corte].copy()

prod = (recente.groupby("produto")
        .apply(lambda g: cpr_anualizada(g["principal_antecipado"].sum()/g["saldo_inicial"].sum()),
               include_groups=False)
        .rename("cpr_produto").reset_index())

seg = (recente.groupby(["produto","segmento"])
       .apply(lambda g: cpr_anualizada(g["principal_antecipado"].sum()/g["saldo_inicial"].sum()),
              include_groups=False)
       .rename("cpr_segmento").reset_index())

resultado = seg.merge(prod, on="produto")
resultado["diferenca_pp"] = (resultado["cpr_segmento"]-resultado["cpr_produto"])*100
resultado["diferenca_abs_pp"] = resultado["diferenca_pp"].abs()
salvar_tabela(resultado, "t02_cpr_segmentacao.csv")

ordem = resultado.sort_values("diferenca_abs_pp", ascending=False)
plt.figure(figsize=(9,5))
rotulos = ordem["produto"] + " / " + ordem["segmento"]
plt.bar(rotulos, ordem["diferenca_abs_pp"])
plt.ylabel("|CPR segmento - CPR produto| (p.p.)")
plt.title("T02 — Heterogeneidade da CPR dentro dos produtos")
plt.xticks(rotation=35, ha="right")
salvar_figura("teste_t02_cpr_segmentacao.png")

print(ordem.to_string(index=False))
