"""
T03 — Risco de base: representatividade do vértice de 252 dias (~1 ano).
"""
from _util import *

pre = pd.read_csv(PASTA_DADOS/"curva_pre_sintetica.csv", parse_dates=["data"])
cupom = pd.read_csv(PASTA_DADOS/"curva_cupom_sintetica.csv", parse_dates=["data"])
base = pre.merge(cupom, on=["data","prazo_anos"])
base["relacao_cupom_pre"] = base["taxa_cupom"]/base["taxa_pre"]

q = base.groupby("prazo_anos")["relacao_cupom_pre"].quantile([0.01,0.99]).unstack()
q.columns = ["p1","p99"]
# mede desvio da razão em relação a 1 (basis relativo), e não o nível bruto da razão
q["severidade"] = np.maximum((q["p1"]-1).abs(), (q["p99"]-1).abs())
ref = q.loc[1.0, "severidade"]
q["erro_relativo_vs_1ano_pct"] = (q["severidade"]/ref - 1).abs()*100
q = q.reset_index()
salvar_tabela(q, "t03_risco_base.csv")

plt.figure(figsize=(9,5))
plt.plot(q["prazo_anos"], q["severidade"]*100, marker="o", label="Por prazo")
plt.axhline(ref*100, linestyle="--", label="Referência de 1 ano")
plt.xlabel("Prazo (anos)")
plt.ylabel("Severidade do basis (%)")
plt.title("T03 — Estrutura a termo do risco de base")
plt.legend()
salvar_figura("teste_t03_risco_base.png")

print(q.to_string(index=False))
