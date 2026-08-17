"""
T10 — Backtest comportamental: CPR e depósitos sem vencimento.
"""
from _util import *

# CPR
cpr = pd.read_csv(PASTA_DADOS/"historico_cpr_sintetico.csv", parse_dates=["data"]).sort_values("data")
cpr["tam_prevista"] = cpr.groupby(["produto","segmento"])["tam_realizada"].transform(
    lambda s: s.shift(1).rolling(6).mean()
)
cpr["erro"] = cpr["tam_realizada"]-cpr["tam_prevista"]
m_cpr = (cpr.dropna().groupby(["produto","segmento"])["erro"]
         .agg(erro_absoluto_medio=lambda s:np.mean(np.abs(s)),
              vies="mean",
              raiz_erro_quadratico_medio=lambda s:np.sqrt(np.mean(s**2)))
         .reset_index())
salvar_tabela(m_cpr,"t10_backtest_cpr.csv")

# DSV: previsão da meia-vida = mediana expansiva das coortes anteriores
dsv = pd.read_csv(PASTA_DADOS/"coortes_depositos_sem_vencimento_sinteticas.csv",
                  parse_dates=["data_coorte"])
def meia_vida(g):
    i=(g["percentual_sobrevivencia"]-0.5).abs().idxmin()
    return g.loc[i,"dia"]
half=(dsv.groupby(["data_coorte","segmento"])
      .apply(meia_vida,include_groups=False).rename("realizada").reset_index()
      .sort_values("data_coorte"))
half["prevista"]=half.groupby("segmento")["realizada"].transform(
    lambda s:s.shift(1).expanding(min_periods=4).median()
)
half["erro"]=half["realizada"]-half["prevista"]
m_dsv=(half.dropna().groupby("segmento")["erro"]
       .agg(erro_absoluto_medio=lambda s:np.mean(np.abs(s)),
            vies="mean",
            raiz_erro_quadratico_medio=lambda s:np.sqrt(np.mean(s**2)))
       .reset_index())
salvar_tabela(m_dsv,"t10_backtest_dsv.csv")

# Figura: viés
fig = pd.concat([
    m_cpr.assign(serie=m_cpr["produto"]+"/"+m_cpr["segmento"])[["serie","vies"]],
    m_dsv.assign(serie="DSV/"+m_dsv["segmento"])[["serie","vies"]]
],ignore_index=True)
plt.figure(figsize=(11,5))
plt.bar(fig["serie"],fig["vies"])
plt.axhline(0,linestyle="--")
plt.ylabel("Viés (unidade original de cada teste)")
plt.title("T10 — Viés dos backtests comportamentais")
plt.xticks(rotation=40,ha="right")
salvar_figura("teste_t10_backtest.png")

print("\nCPR:\n",m_cpr.to_string(index=False))
print("\nDepósitos sem vencimento:\n",m_dsv.to_string(index=False))
