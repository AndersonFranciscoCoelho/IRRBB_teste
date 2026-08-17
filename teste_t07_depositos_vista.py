"""
T07 — Depósitos à vista: sensibilidade ao uso da maior redução histórica.
"""
from _util import *

base = pd.read_csv(PASTA_DADOS/"depositos_a_vista_sinteticos.csv", parse_dates=["data"])
base["saida"] = (-base["variacao_mensal"]).clip(lower=0)

linhas = []
for coop,g in base.groupby("cooperativa"):
    x = g["saida"].to_numpy()
    p95 = np.quantile(x,0.95)
    p99 = np.quantile(x,0.99)
    es95 = x[x>=p95].mean()
    linhas.append([coop,x.max(),p95,p99,es95])

resultado = pd.DataFrame(linhas, columns=["cooperativa","maximo","p95","p99","media_cauda_95"])
resultado["maximo_menos_p99_pp"] = (resultado["maximo"]-resultado["p99"])*100
salvar_tabela(resultado, "t07_depositos_vista_extremos.csv")

ordem = resultado.sort_values("maximo_menos_p99_pp", ascending=False)
plt.figure(figsize=(10,5))
x = np.arange(len(ordem))
largura = 0.38
plt.bar(x-largura/2, ordem["maximo"]*100, largura, label="Máximo")
plt.bar(x+largura/2, ordem["p99"]*100, largura, label="P99")
plt.xticks(x, ordem["cooperativa"], rotation=30, ha="right")
plt.ylabel("Saída mensal (%)")
plt.title("T07 — Máximo histórico versus P99")
plt.legend()
salvar_figura("teste_t07_depositos_vista.png")

print(ordem.to_string(index=False))
