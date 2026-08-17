"""
T08 — Capital próprio: sensibilidade à alocação temporal 6/12/18/24 meses.
Usa a curva Pré sintética mais recente como taxa-base interpolada.
"""
from _util import *

curva = pd.read_csv(PASTA_DADOS/"curva_pre_sintetica.csv", parse_dates=["data"])
ultima = curva[curva["data"]==curva["data"].max()].sort_values("prazo_anos")

def taxa(prazo):
    return np.interp(prazo, ultima["prazo_anos"], ultima["taxa_pre"])

def delta_eve(valor, pesos, prazos, choque=0.03):
    vp0 = sum(valor*w/(1+taxa(t))**t for w,t in zip(pesos,prazos))
    vp1 = sum(valor*w/(1+taxa(t)+choque)**t for w,t in zip(pesos,prazos))
    return vp0, vp1, vp0-vp1

valor = 500_000_000
cenarios = {
    "mais_curto":([0.55,0.25,0.15,0.05],[0.5,1,1.5,2]),
    "tudo_1_ano":([1.0],[1.0]),
    "uniforme_6_12_18_24":([0.25]*4,[0.5,1,1.5,2]),
    "mais_longo":([0.05,0.15,0.30,0.50],[0.5,1,1.5,2]),
}
linhas=[]
for nome,(pesos,prazos) in cenarios.items():
    vp0,vp1,de = delta_eve(valor,pesos,prazos)
    linhas.append([nome,vp0,vp1,de,de/1e6])

resultado = pd.DataFrame(linhas, columns=["cenario","vp_base","vp_estresse","delta_eve","delta_eve_milhoes"])
salvar_tabela(resultado, "t08_capital_proprio.csv")

plt.figure(figsize=(9,5))
plt.bar(resultado["cenario"], resultado["delta_eve_milhoes"])
plt.ylabel("ΔEVE (R$ milhões)")
plt.title("T08 — Sensibilidade do capital próprio")
plt.xticks(rotation=25, ha="right")
salvar_figura("teste_t08_capital_proprio.png")

print(resultado.to_string(index=False))
