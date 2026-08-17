"""Executa todos os testes quantitativos T01 a T10 em sequência."""
from pathlib import Path
import subprocess, sys

pasta = Path(__file__).resolve().parent
testes = sorted(pasta.glob("teste_t*.py"))

falhas = []
for teste in testes:
    print("\n" + "="*80)
    print(f"EXECUTANDO {teste.name}")
    print("="*80)
    proc = subprocess.run([sys.executable, str(teste)], cwd=pasta)
    if proc.returncode != 0:
        falhas.append(teste.name)

if falhas:
    raise SystemExit(f"Falha nos testes: {falhas}")

print("\nTodos os testes foram executados com sucesso.")
