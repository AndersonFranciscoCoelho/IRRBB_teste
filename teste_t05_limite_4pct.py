"""
T05 — Choque interno: frequência e materialidade do limite de 4%.
A série de choque bruto é recalibrada mensalmente usando histórico móvel de 60 meses.
"""
from _util import *

curva = pd.read_csv(PASTA_DADOS/"curva_pre_sintetica.csv", parse_dates=["data"])
painel = curva.pivot(index="data", columns="prazo_anos", values="taxa_pre").sort_index()
mov = painel.pct_change(6)

linhas = []
janela = 60
for i in range(janela, len(mov)):
    hist = mov.iloc[i-janela:i].dropna()
    if hist.empty:
        continue
    choques = []
    for c in hist.columns:
        p1, p99 = hist[c].quantile([0.01,0.99])
        choques.append(max(abs(p1),abs(p99)))
    bruto = np.mean(choques)
    linhas.append([mov.index[i], bruto, min(bruto,0.04)])

resultado = pd.DataFrame(linhas, columns=["data","choque_sem_limite","choque_com_limite"])
resultado["limite_ativo"] = resultado["choque_sem_limite"] > 0.04
resultado["reducao_relativa"] = np.where(
    resultado["choque_sem_limite"]>0,
    1-resultado["choque_com_limite"]/resultado["choque_sem_limite"],0
)
salvar_tabela(resultado, "t05_limite_4pct.csv")

resumo = pd.DataFrame([{
    "media_sem_limite":resultado["choque_sem_limite"].mean(),
    "media_com_limite":resultado["choque_com_limite"].mean(),
    "frequencia_limite_pct":resultado["limite_ativo"].mean()*100,
    "reducao_media_pct":resultado["reducao_relativa"].mean()*100,
}])
salvar_tabela(resumo, "t05_resumo_limite_4pct.csv")

plt.figure(figsize=(10,5))
plt.plot(resultado["data"], resultado["choque_sem_limite"]*100, label="Sem limite")
plt.plot(resultado["data"], resultado["choque_com_limite"]*100, label="Com limite")
plt.axhline(4, linestyle="--", label="Limite de 4%")
plt.ylabel("Choque (%)")
plt.title("T05 — Efeito temporal do limite de 4%")
plt.legend()
salvar_figura("teste_t05_limite_4pct.png")

print(resumo.to_string(index=False))
