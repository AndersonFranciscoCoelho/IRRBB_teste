"""
T04 — Choque interno: média simples dos vértices versus ponderação por DV01.
A severidade por vértice é estimada da curva Pré sintética; o DV01 é aproximado
a partir da carteira sintética.
"""
from _util import *

curva = pd.read_csv(PASTA_DADOS/"curva_pre_sintetica.csv", parse_dates=["data"])
carteira = pd.read_csv(PASTA_DADOS/"carteira_sintetica.csv")

# Variação percentual em aproximadamente seis meses (6 observações mensais)
painel = curva.pivot(index="data", columns="prazo_anos", values="taxa_pre").sort_index()
mov = painel.pct_change(6).dropna()

severidade = pd.DataFrame({
    "prazo_anos": mov.columns,
    "p1": [mov[c].quantile(0.01) for c in mov.columns],
    "p99": [mov[c].quantile(0.99) for c in mov.columns],
})
severidade["choque"] = severidade[["p1","p99"]].abs().max(axis=1)

# DV01 aproximado por instrumento; suficiente como benchmark independente didático.
taxa_ref = 0.10
carteira["dv01_aprox"] = (
    carteira["nocional"].abs()
    * carteira["prazo_anos"]
    / (1 + taxa_ref) ** (carteira["prazo_anos"] + 1)
    * 1e-4
)
dv01 = carteira.groupby("prazo_anos", as_index=False)["dv01_aprox"].sum()

tab = severidade.merge(dv01, on="prazo_anos", how="left").fillna({"dv01_aprox":0})
media_simples = tab["choque"].mean()
media_dv01 = np.average(tab["choque"], weights=np.maximum(tab["dv01_aprox"], 1e-12))
maximo = tab["choque"].max()

resumo = pd.DataFrame({
    "metodo":["media_simples","ponderacao_dv01","maximo"],
    "choque":[media_simples, media_dv01, maximo],
    "choque_pct":[media_simples*100, media_dv01*100, maximo*100]
})
salvar_tabela(tab, "t04_choque_por_vertice.csv")
salvar_tabela(resumo, "t04_resumo_agregacao.csv")

plt.figure(figsize=(8,5))
plt.bar(["Média simples","Ponderação por DV01","Máximo"], resumo["choque_pct"])
plt.ylabel("Choque (%)")
plt.title("T04 — Agregação dos vértices")
salvar_figura("teste_t04_choque_vertices.png")

print(resumo.to_string(index=False))
