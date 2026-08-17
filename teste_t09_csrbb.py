"""
T09 — CSRBB: dependência de um cenário histórico de 21 dias úteis.
"""
from _util import *

base = pd.read_csv(PASTA_DADOS/"spreads_csrbb_sinteticos.csv", parse_dates=["data"])
# Prazo de 1 ano para benchmark de estabilidade entre grupos
p = base[base["prazo_anos"]==1].pivot(index="data",columns="grupo_emissor",values="spread").sort_index()
var21 = p.pct_change(21)

linhas=[]
for grupo in var21.columns:
    s=var21[grupo].dropna()
    pior_data=s.idxmax()
    pior=s.max()
    pos2021=s[s.index>=pd.Timestamp("2021-01-01")]
    pior_pos=pos2021.max()
    linhas.append([grupo,pior_data,pior,pior_pos,pior-pior_pos])

resultado=pd.DataFrame(linhas,columns=["grupo_emissor","data_pior","pior_21d","pior_pos_2021","diferenca"])
salvar_tabela(resultado,"t09_csrbb_21dias.csv")

ordem=resultado.sort_values("pior_21d",ascending=False)
plt.figure(figsize=(9,5))
x=np.arange(len(ordem)); w=0.38
plt.bar(x-w/2,ordem["pior_21d"]*100,w,label="Pior amostra total")
plt.bar(x+w/2,ordem["pior_pos_2021"]*100,w,label="Pior após 2021")
plt.xticks(x,ordem["grupo_emissor"],rotation=30,ha="right")
plt.ylabel("Variação de spread em 21 dias (%)")
plt.title("T09 — CSRBB: estabilidade do cenário histórico")
plt.legend()
salvar_figura("teste_t09_csrbb.png")

print(resultado.to_string(index=False))
