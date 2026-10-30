"""Mede os seis métodos fixos + `ordenar` nos cenários do trabalho.

Uso (da raiz do repositório):
    python -m benchmarks.medir               # n=20000, ~1-2 min
    python -m benchmarks.medir --n 5000      # mais rápido
Saída: tabelas Markdown no terminal + benchmarks/resultados.{md,json}.
Semente fixa (--semente): as listas são idênticas em toda execução.
"""
import argparse
import json
import random
import time

from ordenacao import METODOS, FaixaGrandeDemais, escolher, ordenar
from ordenacao.escolhedor import _planejar
from benchmarks._tempo import medir

ORDEM = ["insercao", "intercalacao", "rapida", "hibrida", "contagem", "base"]


def com_trocas(base_ord, pct, rng):
    v = list(base_ord)
    n = len(v)
    for _ in range(max(1, int(n * pct / 100))):
        i, j = rng.randrange(n), rng.randrange(n)
        v[i], v[j] = v[j], v[i]
    return v


def cenarios(n, semente):
    rng = random.Random(semente)
    ord_grande = sorted(rng.randint(-2**31, 2**31) for _ in range(n))
    chaves5 = [rng.randint(-2**31, 2**31) for _ in range(5)]
    principais = {
        "A. aleatório, chaves grandes": [rng.randint(-2**31, 2**31) for _ in range(n)],
        "B. faixa estreita [-500, 500]": [rng.randint(-500, 500) for _ in range(n)],
        "C. quase ordenado (1% de trocas)": com_trocas(ord_grande, 1.0, rng),
        "D. lista minúscula (n=16)": [rng.randint(-10**6, 10**6) for _ in range(16)],
    }
    extras = {
        "E. 5 chaves distintas em faixa de 2^32": [rng.choice(chaves5) for _ in range(n)],
        "F. quase ordenado (0,3% de trocas)": com_trocas(ord_grande, 0.3, rng),
    }
    return principais, extras


def fmt(t):
    if t is None:
        return "recusa (faixa)"
    ms = t * 1e3
    return f"{ms:.1f}" if ms >= 1 else f"{ms:.4f}"


def medir_cenario(v, repeticoes=9):
    r = {"n": len(v), "t": {}}
    for nome in ORDEM:
        f = METODOS[nome]
        try:
            r["t"][nome] = medir(f, v, repeticoes=repeticoes)
        except FaixaGrandeDemais:
            r["t"][nome] = None
    r["t"]["sorted()"] = medir(sorted, v, repeticoes=repeticoes)
    r["t"]["ordenar"] = medir(ordenar, v, repeticoes=repeticoes)
    r["t_escolher"] = medir(escolher, v, repeticoes=repeticoes)
    r["escolha"] = escolher(v)
    return r


def tabela(resultados):
    cols = ORDEM + ["ordenar"]
    linhas = ["| cenário | " + " | ".join(cols) + " | sorted() (ref.) |",
              "|---|" + "---:|" * (len(cols) + 1)]
    for nome, r in resultados.items():
        fixos = {k: r["t"][k] for k in ORDEM if r["t"][k] is not None}
        melhor = min(fixos, key=fixos.get)
        cel = []
        for c in cols:
            s = fmt(r["t"][c])
            cel.append(f"**{s}**" if c == melhor else s)
        linhas.append(f"| {nome} | " + " | ".join(cel) + f" | {fmt(r['t']['sorted()'])} |")
    return "\n".join(linhas)


def tabela_decisao(resultados):
    linhas = ["| cenário | escolheu | melhor fixo | ordenar ÷ melhor | escolher (ms) | escolher ÷ ordenar |",
              "|---|---|---|---:|---:|---:|"]
    for nome, r in resultados.items():
        fixos = {k: r["t"][k] for k in ORDEM if r["t"][k] is not None}
        melhor = min(fixos, key=fixos.get)
        razao = r["t"]["ordenar"] / fixos[melhor]
        custo = r["t_escolher"] / r["t"]["ordenar"]
        linhas.append(f"| {nome} | {r['escolha']} | {melhor} | {razao:.2f}× "
                      f"| {r['t_escolher'] * 1e3:.4f} | {custo:.1%} |")
    return "\n".join(linhas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20000)
    ap.add_argument("--semente", type=int, default=2024)
    args = ap.parse_args()

    principais, extras = cenarios(args.n, args.semente)
    res_p, res_e = {}, {}
    for nome, v in principais.items():
        print("medindo", nome, flush=True)
        res_p[nome] = medir_cenario(v)
    for nome, v in extras.items():
        print("medindo", nome, flush=True)
        res_e[nome] = medir_cenario(v)

    saida = ["# Resultados (tempo mediano de uma chamada, em ms)\n",
             f"n = {args.n} nos cenários A, B, C, E, F; semente {args.semente}. "
             "Em negrito, o mais rápido entre os seis métodos fixos.\n",
             "## Cenários principais\n", tabela(res_p), "",
             "### Decisão do `escolher` e custo\n", tabela_decisao(res_p), "",
             "## Cenários extras (onde o `escolher` pode errar)\n",
             tabela(res_e), "", tabela_decisao(res_e), ""]
    texto = "\n".join(saida)
    print("\n" + texto)
    with open("benchmarks/resultados.md", "w", encoding="utf-8") as f:
        f.write(texto)
    with open("benchmarks/resultados.json", "w", encoding="utf-8") as f:
        json.dump({"n": args.n, "semente": args.semente,
                   "principais": res_p, "extras": res_e}, f, indent=1)


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"\n(total {time.time() - t0:.0f}s)")
