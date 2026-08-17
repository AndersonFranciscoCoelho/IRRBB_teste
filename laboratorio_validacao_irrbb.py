"""Laboratório quantitativo de validação de IRRBB com dados sintéticos.\nArquivo exportado do Jupyter Notebook para facilitar revisão e execução.\n"""\n

# %%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

PASTA = Path(".")
pd.set_option("display.float_format", lambda x: f"{x:,.6f}")


# %%
curva_pre = pd.read_csv(PASTA/"curva_pre_sintetica.csv", parse_dates=["data"])
curva_cupom = pd.read_csv(PASTA/"curva_cupom_sintetica.csv", parse_dates=["data"])
historico_cpr = pd.read_csv(PASTA/"historico_cpr_sintetico.csv", parse_dates=["data"])
depositos_sem_vencimento = pd.read_csv(PASTA/"coortes_depositos_sem_vencimento_sinteticas.csv", parse_dates=["data_coorte"])
depositos_a_vista = pd.read_csv(PASTA/"depositos_a_vista_sinteticos.csv", parse_dates=["data"])
carteira = pd.read_csv(PASTA/"carteira_sintetica.csv")
spreads_csrbb = pd.read_csv(PASTA/"spreads_csrbb_sinteticos.csv", parse_dates=["data"])

display(carteira.head())


# %%
def cpr_anualizada_da_tam(tam):
    return (1 + tam)**12 - 1

def calcular_cpr_movel(df, janela):
    x = (df.sort_values("data")
           .groupby(["produto","segmento"], group_keys=False)
           .apply(lambda g: g.assign(
               tam_est=g["principal_antecipado"].rolling(janela).sum() /
                       g["saldo_inicial"].rolling(janela).sum()
           )))
    x["cpr_est"] = cpr_anualizada_da_tam(x["tam_est"])
    x["janela"] = janela
    return x

comparacao_janelas = pd.concat([calcular_cpr_movel(historico_cpr, w) for w in [3,6,12,24,36]], ignore_index=True)
ultima_observacao = (comparacao_janelas.dropna()
          .sort_values("data")
          .groupby(["produto","segmento","janela"])
          .tail(1))

tabela_cpr = ultima_observacao.pivot_table(index=["produto","segmento"], columns="janela", values="cpr_est")
tabela_cpr.columns = [f"CPR_{c}m" for c in tabela_cpr.columns]
tabela_cpr["amplitude_pp"] = (tabela_cpr.max(axis=1) - tabela_cpr.min(axis=1))*100
display(tabela_cpr.sort_values("amplitude_pp", ascending=False))


# %%
exemplo = comparacao_janelas.query("produto == 'Veiculos' and segmento == 'PF_A'").dropna()
for w in [3,6,12,24,36]:
    s = exemplo[exemplo["janela"]==w]
    plt.plot(s["data"], s["cpr_est"], label=f"{w} meses")
plt.title("CPR estimada por janela — Veículos / PF_A")
plt.ylabel("CPR anualizada")
plt.legend()
plt.show()


# %%
recente = historico_cpr[historico_cpr["data"] >= historico_cpr["data"].max() - pd.DateOffset(months=12)].copy()
cpr_por_produto = recente.groupby("produto").apply(
    lambda g: cpr_anualizada_da_tam(g["principal_antecipado"].sum()/g["saldo_inicial"].sum())
).rename("cpr_produto")
cpr_por_segmento = recente.groupby(["produto","segmento"]).apply(
    lambda g: cpr_anualizada_da_tam(g["principal_antecipado"].sum()/g["saldo_inicial"].sum())
).rename("cpr_segmento").reset_index()

comparacao_segmentacao = cpr_por_segmento.merge(cpr_por_produto.reset_index(), on="produto")
comparacao_segmentacao["diferenca_pp"] = (comparacao_segmentacao["cpr_segmento"] - comparacao_segmentacao["cpr_produto"])*100
display(comparacao_segmentacao.sort_values("diferenca_pp", key=abs, ascending=False))


# %%
risco_base = curva_cupom.merge(curva_pre, on=["data","prazo_anos"])
risco_base["relacao_cupom_pre"] = risco_base["taxa_cupom"] / risco_base["taxa_pre"]

q = risco_base.groupby("prazo_anos")["relacao_cupom_pre"].quantile([0.01,0.99]).unstack()
q.columns = ["P1","P99"]
q["choque_referencia"] = q.abs().max(axis=1)
q["choque_1_ano"] = q.loc[1.0,"choque_referencia"]
q["erro_relativo_vs_1_ano"] = q["choque_1_ano"]/q["choque_referencia"] - 1
display(q)


# %%
plt.plot(q.index, q["choque_referencia"], marker="o", label="Por prazo")
plt.axhline(q.loc[1.0,"choque_referencia"], linestyle="--", label="Referência de 1 ano")
plt.xlabel("Prazo em anos")
plt.ylabel("Máx(|P1|, |P99|) da razão cupom/pré")
plt.title("Dependência do risco_base com o prazo")
plt.legend()
plt.show()


# %%
def meia_vida_observada(g):
    g = g.sort_values("dia")
    idx = (g["percentual_sobrevivencia"] - 0.5).abs().idxmin()
    return g.loc[idx, "dia"]

meias_vidas = (depositos_sem_vencimento.groupby(["data_coorte","segmento"])
        .apply(meia_vida_observada)
        .rename("meia_vida_dias")
        .reset_index())

display(meias_vidas.groupby("segmento")["meia_vida_dias"].agg(media="mean", desvio_padrao="std", minimo="min", maximo="max"))


# %%
for seg in meias_vidas["segmento"].unique():
    s = meias_vidas[meias_vidas["segmento"]==seg]
    plt.plot(s["data_coorte"], s["meia_vida_dias"], marker="o", label=seg)
plt.ylabel("Meia-vida observada (dias)")
plt.title("Variação temporal dos depósitos sem vencimento")
plt.legend()
plt.show()


# %%
vertices = pd.DataFrame({
    "prazo_anos":[0.25,0.5,1,2,5,7,10,15,20],
    "choque":[0.105,0.080,0.055,0.040,0.030,0.025,0.022,0.020,0.018],
    "dv01":[40,35,30,25,15,8,5,2,1]
})

media_simples = vertices["choque"].mean()
choque_maximo = vertices["choque"].max()
media_ponderada_dv01 = np.average(vertices["choque"], weights=vertices["dv01"])

comparacao_choque = pd.DataFrame({
    "metodo":["Média simples","Máximo","Média ponderada por DV01"],
    "choque":[media_simples,choque_maximo,media_ponderada_dv01]
})
display(comparacao_choque)


# %%
plt.plot(vertices["prazo_anos"], vertices["choque"], marker="o")
plt.axhline(media_simples, linestyle="--", label="Média simples")
plt.axhline(media_ponderada_dv01, linestyle=":", label="Média ponderada por DV01")
plt.xlabel("Prazo em anos")
plt.ylabel("Choque")
plt.title("Choque por vértice")
plt.legend()
plt.show()


# %%
choques_sem_limite = pd.Series(np.random.default_rng(123).lognormal(mean=np.log(0.032), sigma=0.40, size=120), name="choque_sem_limite")
limite = 0.04
choques_limitados = choques_sem_limite.clip(upper=limite)

estatisticas_limite = pd.Series({
    "média_sem_limite":choques_sem_limite.mean(),
    "média_com_limite":choques_limitados.mean(),
    "percentual_meses_limite_ativo":(choques_sem_limite>limite).mean(),
    "máximo_sem_limite":choques_sem_limite.max(),
    "redução_média_relativa":1-choques_limitados.mean()/choques_sem_limite.mean()
})
display(estatisticas_limite.to_frame("valor"))


# %%
saidas = depositos_a_vista.assign(saida=(-depositos_a_vista["variacao_mensal"]).clip(lower=0))
linhas = []
for cooperativa,g in saidas.groupby("cooperativa"):
    valores = g["saida"].values
    p95 = np.quantile(valores,0.95)
    p99 = np.quantile(valores,0.99)
    es95 = valores[valores>=p95].mean()
    linhas.append([cooperativa, valores.max(), p95, p99, es95])
estatisticas_depositos = pd.DataFrame(linhas, columns=["cooperativa","maximo","p95","p99","media_cauda_95"])
estatisticas_depositos["diferenca_maximo_p99_pp"] = (estatisticas_depositos["maximo"]-estatisticas_depositos["p99"])*100
display(estatisticas_depositos.sort_values("diferenca_maximo_p99_pp", ascending=False))


# %%
def valor_presente_fluxos(valor_pl, pesos, prazos, taxa_base=0.10, choque=0.03):
    vp_base = sum(valor_pl*w/((1+taxa_base)**t) for w,t in zip(pesos,prazos))
    vp_estresse = sum(valor_pl*w/((1+taxa_base+choque)**t) for w,t in zip(pesos,prazos))
    return vp_base, vp_estresse, vp_base-vp_estresse

valor_pl = 500_000_000
cenarios_pl = {
    "Uniforme 6/12/18/24m":([0.25]*4,[0.5,1,1.5,2]),
    "Mais curto":([0.55,0.25,0.15,0.05],[0.5,1,1.5,2]),
    "Mais longo":([0.05,0.15,0.30,0.50],[0.5,1,1.5,2]),
    "Tudo 1 ano":([1.0],[1.0]),
    "Sem PL":([0.0],[1.0])
}
resultado=[]
for nome,(pesos,prazos) in cenarios_pl.items():
    vp_base,vp_estresse,delta_eve = valor_presente_fluxos(valor_pl,pesos,prazos)
    resultado.append([nome,vp_base,vp_estresse,delta_eve])
sensibilidade_pl = pd.DataFrame(resultado,columns=["cenario","vp_base","vp_estresse","delta_eve"])
display(sensibilidade_pl)


# %%
csrbb_1_ano = spreads_csrbb[spreads_csrbb["prazo_anos"]==1].pivot(index="data",columns="grupo_emissor",values="spread").sort_index()
variacao_21_dias = csrbb_1_ano.pct_change(21)

resumo_csrbb=[]
for cl in variacao_21_dias.columns:
    s=variacao_21_dias[cl].dropna()
    data_pior=s.idxmax()
    pior=s.max()
    pior_pos_2021=s[s.index>=pd.Timestamp("2021-01-01")].max()
    resumo_csrbb.append([cl,data_pior,pior,pior_pos_2021,pior-pior_pos_2021])
resumo_csrbb=pd.DataFrame(resumo_csrbb,columns=["grupo_emissor","data_pior","pior_21_dias","pior_pos_2021","diferenca"])
display(resumo_csrbb)


# %%
# CPR: previsão simples com média móvel 6m versus realizado
cpr_teste = historico_cpr.sort_values("data").copy()
cpr_teste["tam_prevista_6m"] = (
    cpr_teste.groupby(["produto","segmento"])["tam_realizada"]
          .transform(lambda s: s.shift(1).rolling(6).mean())
)
cpr_teste["erro"] = cpr_teste["tam_realizada"] - cpr_teste["tam_prevista_6m"]

metricas_cpr = (cpr_teste.dropna()
               .groupby(["produto","segmento"])["erro"]
               .agg(erro_absoluto_medio=lambda s: np.mean(np.abs(s)),
                    vies="mean",
                    raiz_erro_quadratico_medio=lambda s: np.sqrt(np.mean(s**2))))
display(metricas_cpr)


# %%
# Depositos_Sem_Vencimento: compara meia-vida da coorte com a mediana histórica anterior
meias_vidas = meias_vidas.sort_values("data_coorte")
meias_vidas["meia_vida_prevista"] = (
    meias_vidas.groupby("segmento")["meia_vida_dias"]
        .transform(lambda s: s.shift(1).expanding(min_periods=4).median())
)
meias_vidas["erro_dias"] = meias_vidas["meia_vida_dias"] - meias_vidas["meia_vida_prevista"]

metricas_depositos=(meias_vidas.dropna()
             .groupby("segmento")["erro_dias"]
             .agg(erro_absoluto_medio=lambda s: np.mean(np.abs(s)),
                  vies="mean",
                  raiz_erro_quadratico_medio=lambda s: np.sqrt(np.mean(s**2))))
display(metricas_depositos)


# %%
quadro_resumo = []

# CPR instability
maior_amplitude_cpr = float(tabela_cpr["amplitude_pp"].max())
quadro_resumo.append(["CPR - janela de estimação", maior_amplitude_cpr, "pp de faixa entre janelas",
                  "ALTO" if maior_amplitude_cpr>5 else "MÉDIO" if maior_amplitude_cpr>2 else "BAIXO"])

# Basis
maior_erro_risco_base = float(q["erro_relativo_vs_1_ano"].abs().max()*100)
quadro_resumo.append(["Risco de base - referência de 1 ano", maior_erro_risco_base, "% erro relativo vs estrutura a termo",
                  "ALTO" if maior_erro_risco_base>15 else "MÉDIO" if maior_erro_risco_base>7 else "BAIXO"])

# Depositos_Sem_Vencimento drift
dispersao_nmd = float(meias_vidas.groupby("segmento")["meia_vida_dias"].mean().std())
quadro_resumo.append(["Depósitos sem vencimento - estabilidade temporal", dispersao_nmd, "dispersão entre segmentos/coortes",
                  "ALTO" if dispersao_nmd>100 else "MÉDIO"])

# Shock averaging
diluicao = float((media_ponderada_dv01-media_simples)*100)
quadro_resumo.append(["Choque interno - média simples", diluicao, "p.p. versus ponderação por DV01",
                  "ALTO" if abs(diluicao)>1 else "MÉDIO"])

# Cap
percentual_limite_ativo = float((choques_sem_limite>limite).mean()*100)
quadro_resumo.append(["Choque interno - limite de 4%", percentual_limite_ativo, "% de meses com limite ativo",
                  "ALTO" if percentual_limite_ativo>25 else "MÉDIO" if percentual_limite_ativo>10 else "BAIXO"])

# DD max
maior_gap_depositos = float(estatisticas_depositos["diferenca_maximo_p99_pp"].max())
quadro_resumo.append(["Depósitos à vista - máximo histórico", maior_gap_depositos, "p.p. entre máximo e P99",
                  "ALTO" if maior_gap_depositos>5 else "MÉDIO"])

# Capital
amplitude_pl = float((sensibilidade_pl["delta_eve"].max()-sensibilidade_pl["delta_eve"].min())/1e6)
quadro_resumo.append(["Capital próprio - alocação", amplitude_pl, "R$ milhões de amplitude em ΔEVE",
                  "ALTO" if amplitude_pl>10 else "MÉDIO"])

quadro_resumo = pd.DataFrame(quadro_resumo, columns=["tema","indicador","unidade","criticidade"])
display(quadro_resumo)
