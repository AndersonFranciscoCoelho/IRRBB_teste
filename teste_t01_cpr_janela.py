"""
T01 — CPR: sensibilidade à janela histórica.
Premissa desafiada: utilização de seis meses para estimar a TAM/CPR.
"""
from _util import *

base = pd.read_csv(PASTA_DADOS/"historico_cpr_sintetico.csv", parse_dates=["data"])
janelas = [3, 6, 12, 24, 36]

def calcular(base, janela):
    partes = []
    for (produto, segmento), g in base.groupby(["produto", "segmento"]):
        g = g.sort_values("data").copy()
        g["tam_estimada"] = (
            g["principal_antecipado"].rolling(janela).sum()
            / g["saldo_inicial"].rolling(janela).sum()
        )
        g["cpr_estimada"] = cpr_anualizada(g["tam_estimada"])
        g["janela_meses"] = janela
        partes.append(g)
    return pd.concat(partes, ignore_index=True)

resultado = pd.concat([calcular(base, j) for j in janelas], ignore_index=True)
ultima = (resultado.dropna().sort_values("data")
          .groupby(["produto","segmento","janela_meses"]).tail(1))

tabela = ultima.pivot_table(index=["produto","segmento"],
                            columns="janela_meses",
                            values="cpr_estimada")
tabela.columns = [f"cpr_{int(c)}m" for c in tabela.columns]
cols_cpr = list(tabela.columns)
tabela["amplitude_pp"] = (tabela[cols_cpr].max(axis=1)-tabela[cols_cpr].min(axis=1))*100
tabela = tabela.reset_index()
salvar_tabela(tabela, "t01_cpr_janelas.csv")

# Segmento com maior sensibilidade
alvo = tabela.sort_values("amplitude_pp", ascending=False).iloc[0]
produto, segmento = alvo["produto"], alvo["segmento"]
serie = resultado[(resultado["produto"]==produto)&(resultado["segmento"]==segmento)].dropna()

plt.figure(figsize=(9,5))
for j in janelas:
    s = serie[serie["janela_meses"]==j]
    plt.plot(s["data"], s["cpr_estimada"]*100, label=f"{j} meses")
plt.title(f"T01 — CPR por janela: {produto} / {segmento}")
plt.ylabel("CPR anualizada (%)")
plt.xlabel("Data")
plt.legend()
salvar_figura("teste_t01_cpr_janelas.png")

print("\nMaior amplitude entre janelas:")
print(tabela.sort_values("amplitude_pp", ascending=False).head(5).to_string(index=False))
