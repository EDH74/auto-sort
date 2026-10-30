"""Gera os relatórios do trabalho: arquivos .csv e um gráfico .png.

Uso (da raiz do repositório):
    python -m benchmarks.gerar_relatorios                  # n=20000, ~2-3 min
    python -m benchmarks.gerar_relatorios --rapido         # n=3000, ~20 s
    python -m benchmarks.gerar_relatorios --excel          # CSV com ';' e vírgula decimal
    python -m benchmarks.gerar_relatorios --saida minha_pasta --semente 7

Arquivos gerados em --saida (padrão: relatorios/):
    01_testes_borda.csv        vazia, 1 elemento, iguais, ordenada, invertida, negativos...
    02_tabela_cenarios.csv     4 cenários x 6 métodos (+ ordenar, + sorted() de referência)
    03_vencedores.csv          quem venceu cada cenário e por quê
    04_regras_escolher.csv     regras do `escolher` e de onde vieram
    05_custo_escolher.csv      quanto custa olhar a lista, por tamanho
    06_cenario_de_erro.csv     cenários em que o `escolher` erra a decisão
    07_pior_caso_relativo.csv  pior caso de cada método (vale a pena usar o escolher?)
    relatorio.png              gráfico com os quatro painéis

O gráfico precisa de matplotlib (opcional). Sem ele, só os CSVs são gerados.
Código de saída: 0 se todos os testes de borda passaram, 1 caso contrário.
"""
import argparse
import csv
import math
import os
import random
import sys
import time

from ordenacao import METODOS, FaixaGrandeDemais, escolher, ordenar
from ordenacao import escolhedor as esc
from ordenacao import metodos as met
from benchmarks._tempo import medir
from benchmarks.medir import ORDEM, cenarios, medir_cenario

LIMIAR_ERRO = 1.3     # `ordenar` é considerado "errou" se ficar >= 1,3x atrás do melhor fixo


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------
def _fmt(v, excel):
    if isinstance(v, float):
        s = f"{v:.4f}" if abs(v) < 100 else f"{v:.2f}"
        return s.replace(".", ",") if excel else s
    return v


def escrever_csv(caminho, campos, linhas, excel=False):
    with open(caminho, "w", newline="", encoding="utf-8-sig" if excel else "utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";" if excel else ",", lineterminator="\n")
        w.writeheader()
        for l in linhas:
            w.writerow({k: _fmt(l.get(k, ""), excel) for k in campos})


# ---------------------------------------------------------------------------
# 1. Testes de borda
# ---------------------------------------------------------------------------
CASOS_PEQUENOS = {
    "lista_vazia": [],
    "um_elemento": [7],
    "dois_elementos": [2, 1],
    "todos_iguais": [5] * 50,
    "ja_ordenada": list(range(100)),
    "invertida": list(range(100, 0, -1)),
    "valores_negativos": [-3, 5, -10, 0, 7, -1, -10, 2],
    "so_negativos": [-5, -1, -9, -3, -3],
}


def casos_grandes():
    """Mesmos tipos de caso, com n grande o bastante para o `escolher` sair da
    inserção e passar por contagem / intercalação / base / híbrida."""
    n = 2000
    rng = random.Random(1)
    return {
        "todos_iguais_n2000": [9] * n,
        "ja_ordenada_n2000": list(range(n)),
        "ja_ordenada_chaves_grandes_n2000": list(range(0, n * 10**6, 10**6)),
        "invertida_n2000": list(range(n, 0, -1)),
        "invertida_chaves_grandes_n2000": list(range(n * 10**6, 0, -10**6)),
        "negativos_faixa_estreita_n2000": [rng.randint(-50, 50) for _ in range(n)],
        "negativos_chaves_grandes_n2000": [rng.randint(-2**31, 0) for _ in range(n)],
    }


def testes_de_borda():
    linhas, falhas = [], 0
    todos = dict(METODOS, ordenar=ordenar)
    casos = dict(CASOS_PEQUENOS, **casos_grandes())
    for caso, v in casos.items():
        esperado = sorted(v)
        escolha = escolher(v)
        for nome, f in todos.items():
            copia = list(v)
            try:
                saida = f(v)
                if saida != esperado:
                    res = "FALHOU: saida incorreta"
                elif v != copia:
                    res = "FALHOU: modificou a entrada"
                else:
                    res = "OK"
            except FaixaGrandeDemais:
                # recusa por projeto: faixa grande demais para a contagem
                res = "OK (recusa por projeto: faixa grande)" if nome == "contagem" else "FALHOU: recusa inesperada"
            except Exception as e:                       # noqa: BLE001
                res = f"FALHOU: {type(e).__name__}: {e}"
            falhas += res.startswith("FALHOU")
            linhas.append({"caso": caso, "n": len(v), "metodo": nome,
                           "resultado": res, "escolher_escolheu": escolha})
    return linhas, falhas


# ---------------------------------------------------------------------------
# 2-3. Cenários, vencedores e "por quê"
# ---------------------------------------------------------------------------
def melhor_fixo(r):
    fixos = {k: r["t"][k] for k in ORDEM if r["t"][k] is not None}
    nome = min(fixos, key=fixos.get)
    return nome, fixos[nome]


def _milhar(x):
    return f"{x:,}".replace(",", ".")


def por_que(vencedor, v):
    n = len(v)
    lo, hi = min(v), max(v)
    k = hi - lo + 1
    passadas = ((hi - lo).bit_length() + 7) // 8
    niveis = max(1, round(math.log2(n))) if n > 1 else 1
    if vencedor == "base":
        extra = ""
        if k > met.LIMITE_FAIXA_CONTAGEM:
            extra = (f"; a contagem se recusa (faixa de {_milhar(k)} valores ~ {k * 8 / 1e9:.0f} GB "
                     f"de vetor de contagem)")
        return (f"{passadas} passadas lineares de base 256 contra ~{niveis} níveis de comparações "
                f"em Python; a base ignora o grau de ordem dos dados{extra}")
    if vencedor == "contagem":
        return (f"faixa k={_milhar(k)} pequena diante de n={_milhar(n)}: custo O(n+k) sem nenhuma comparação")
    if vencedor in ("insercao", "hibrida") and n <= esc.N_MINUSCULA:
        return (f"n={n} cabe abaixo do corte da híbrida: sem recursão, baldes ou vetor de contagem; "
                f"inserção e híbrida são o mesmo código aqui, a diferença é ruído "
                f"(a contagem alocaria {_milhar(k)} posições para {n} números)")
    if vencedor == "insercao":
        return "dado praticamente ordenado: a inserção custa O(n + inversões)"
    if vencedor == "intercalacao":
        return "atalho 'metades já ordenadas' torna a intercalação ~O(n) em dado ordenado"
    if vencedor in ("rapida", "hibrida"):
        return ("poucas chaves distintas: a partição em 3 vias custa ~O(n log d), "
                "d = número de valores distintos")
    return "mais rápido nesta medição"


def linha_cenario(nome, v, r):
    venc, tv = melhor_fixo(r)
    t = r["t"]
    return {
        "cenario": nome, "n": r["n"],
        "insercao_ms": _ms(t["insercao"]), "intercalacao_ms": _ms(t["intercalacao"]),
        "rapida_ms": _ms(t["rapida"]), "hibrida_ms": _ms(t["hibrida"]),
        "contagem_ms": _ms(t["contagem"]), "base_ms": _ms(t["base"]),
        "ordenar_ms": _ms(t["ordenar"]), "sorted_referencia_ms": _ms(t["sorted()"]),
        "vencedor_fixo": venc, "escolher_escolheu": r["escolha"],
        "ordenar_sobre_melhor": t["ordenar"] / tv,
        "escolher_ms": r["t_escolher"] * 1e3,
        "escolher_sobre_ordenar_pct": 100 * r["t_escolher"] / t["ordenar"],
    }


def _ms(t):
    return "recusa" if t is None else t * 1e3


# ---------------------------------------------------------------------------
# 4. Regras do escolher (lidas das constantes reais do código)
# ---------------------------------------------------------------------------
def regras():
    return [
        {"ordem": 1, "regra": "n <= N_MINUSCULA -> insercao (sem olhar a lista)",
         "limiar": f"N_MINUSCULA={esc.N_MINUSCULA}",
         "origem": "calibrar [2]: até ~32 elementos inserção e híbrida empatam; de n=48 em diante a inserção perde 1,3x a 4x",
         "tipo_da_origem": "medido"},
        {"ordem": 2, "regra": "elementos amostrados nao sao int -> hibrida",
         "limiar": "type(x) is int em ~256 posições",
         "origem": "contagem e base indexam por valor, só servem a inteiros",
         "tipo_da_origem": "teoria"},
        {"ordem": 3, "regra": "k=max-min+1; k <= RAZAO_CONTAGEM*n e k <= FAIXA_MAX_CONTAGEM -> contagem",
         "limiar": f"RAZAO_CONTAGEM={esc.RAZAO_CONTAGEM}; FAIXA_MAX_CONTAGEM={esc.FAIXA_MAX_CONTAGEM}",
         "origem": "razão 4: calibrar [3] (contagem ganha até k/n~4, base ganha de k/n=8). Teto de 4 milhões "
                   "(~32 MB): trava de memória, prevista ANTES de chamar a contagem",
         "tipo_da_origem": "medido (razão) / decisão de projeto (teto)"},
        {"ordem": 4, "regra": "0 descidas em AMOSTRA pares adjacentes -> intercalacao",
         "limiar": f"AMOSTRA={esc.AMOSTRA}",
         "origem": "calibrar [5]: com o atalho de metades ordenadas a intercalação é ~O(n) em dado ordenado; "
                   "inserção seria mais rápida, mas até 4x pior que a intercalação se a amostra enganar. "
                   "Amostra subiu de 64 para 256 após o erro no cenário C",
         "tipo_da_origem": "medido + ajuste após erro"},
        {"ordem": 5, "regra": "n >= N_MIN_BASE e passadas <= MAX_PASSADAS_BASE -> base",
         "limiar": f"N_MIN_BASE={esc.N_MIN_BASE}; MAX_PASSADAS_BASE={esc.MAX_PASSADAS_BASE}",
         "origem": "calibrar [4]: base perde em n=200 e ganha em n>=1000; o cruzamento está entre os dois "
                   "(512 é um chute dentro do intervalo). 6 passadas é a maior largura testada",
         "tipo_da_origem": "medido (intervalo) / chute dentro do intervalo"},
        {"ordem": 6, "regra": "senao -> hibrida", "limiar": f"CORTE_HIBRIDA={met.CORTE_HIBRIDA}",
         "origem": "melhor método por comparação em todas as tabelas; corte 8-64 indistinguível (ruído)",
         "tipo_da_origem": "medido"},
    ]


# ---------------------------------------------------------------------------
# 5. Custo do escolher
# ---------------------------------------------------------------------------
def varrer_custo(tamanhos, semente, rep):
    rng = random.Random(semente + 1)
    geradores = (("chaves_grandes", lambda n: [rng.randint(-2**31, 2**31) for _ in range(n)]),
                 ("faixa_estreita", lambda n: [rng.randint(-500, 500) for _ in range(n)]))
    linhas = []
    for tipo, gen in geradores:
        for n in tamanhos:
            v = gen(n)
            t_mm = medir(lambda: (min(v), max(v)), repeticoes=rep)
            t_es = medir(escolher, v, repeticoes=rep)
            t_or = medir(ordenar, v, repeticoes=min(rep, 5))
            linhas.append({
                "tipo_de_dados": tipo, "n": n, "escolheu": escolher(v),
                "min_max_ms": t_mm * 1e3, "escolher_ms": t_es * 1e3,
                "ordenar_ms": t_or * 1e3, "custo_pct": 100 * t_es / t_or,
                "ns_por_elemento": t_es * 1e9 / n})
    return linhas


# ---------------------------------------------------------------------------
# 6. Cenários de erro
# ---------------------------------------------------------------------------
EXPLICA_ERRO = {
    "E": ("O escolher só enxerga a FAIXA (máx-mín ~ 4,3e9), que descarta a contagem e aponta para a base. "
          "Não vê que há poucos valores distintos, e a partição em 3 vias da rápida/híbrida custa ~O(n log d). "
          "Contar distintos exigiria um set(), uma passada com hash, não barata."),
    "F": ("Quando ocorre: com poucas trocas, os pares adjacentes amostrados podem ser todos crescentes: o escolher vê "
          "'0 descidas' e escolhe intercalação em vez de base. A amostra é probabilística; a perda é limitada (2x a 4x)."),
}


def linhas_erro(extras_res, principais_res):
    linhas = []
    for nome, r in list(extras_res.items()) + list(principais_res.items()):
        melhor, tm = melhor_fixo(r)
        escolhido = r["escolha"]
        t_escolhido = r["t"].get(escolhido)
        perda = r["t"]["ordenar"] / tm
        errou = (escolhido != melhor) and perda >= LIMIAR_ERRO
        if nome[0] in EXPLICA_ERRO or errou:
            linhas.append({
                "cenario": nome, "escolheu": escolhido, "melhor_fixo": melhor,
                "tempo_do_escolhido_ms": _ms(t_escolhido) if t_escolhido is not None else "",
                "tempo_do_melhor_ms": tm * 1e3,
                "ordenar_ms": r["t"]["ordenar"] * 1e3,
                "perda_x": perda, "errou": "SIM" if errou else "nao (nesta medição)",
                "por_que": EXPLICA_ERRO.get(nome[0], "ver RELATORIO.md")})
    return linhas


# ---------------------------------------------------------------------------
# 7. Pior caso relativo / compensa?
# ---------------------------------------------------------------------------
def pior_caso(principais_res):
    nomes = list(principais_res)
    linhas, piores = [], {}
    for m in ORDEM + ["ordenar"]:
        razoes, falha = {}, False
        for nome in nomes:
            r = principais_res[nome]
            t = r["t"][m]
            if t is None:
                falha = True
                razoes[nome[0]] = "recusa"
            else:
                razoes[nome[0]] = t / melhor_fixo(r)[1]
        validas = [x for x in razoes.values() if x != "recusa"]
        piores[m] = max(validas)
        linha = {"metodo": m, "pior_caso_x": max(validas),
                 "recusou_em_algum_cenario": "SIM" if falha else "nao"}
        for letra, x in razoes.items():
            linha[f"cenario_{letra}"] = x
        linhas.append(linha)
    return linhas, piores


# ---------------------------------------------------------------------------
# Gráfico
# ---------------------------------------------------------------------------
def desenhar(principais_res, extras_res, custo, piores, caminho):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib não instalado: gráfico não gerado (pip install matplotlib).")
        return False

    series = ORDEM + ["ordenar"]
    cores = {"insercao": "#9e9e9e", "intercalacao": "#8c6bb1", "rapida": "#f4a582",
             "hibrida": "#d6604d", "contagem": "#4393c3", "base": "#2ca25f", "ordenar": "#111111"}
    fig, ax = plt.subplots(2, 2, figsize=(16, 10.5))

    def barras(a, resultados, titulo):
        nomes = list(resultados)
        larg = 0.8 / len(series)
        for i, m in enumerate(series):
            xs, ys = [], []
            for j, nome in enumerate(nomes):
                t = resultados[nome]["t"][m]
                x = j + (i - len(series) / 2 + 0.5) * larg
                if t is None:
                    a.plot(x, 3e-4, marker="x", color="red", ms=7, ls="none")
                else:
                    xs.append(x)
                    ys.append(t * 1e3)
            a.bar(xs, ys, width=larg, color=cores[m], label=m,
                  edgecolor="black" if m == "ordenar" else "none", linewidth=1.2)
        a.set_yscale("log")
        a.set_xticks(range(len(nomes)))
        a.set_xticklabels([n.split(" (")[0].replace(". ", ".\n", 1) for n in nomes], fontsize=8)
        a.set_ylabel("tempo por chamada (ms, escala log)")
        a.set_title(titulo, fontsize=10)
        a.grid(axis="y", alpha=0.3)

    barras(ax[0][0], principais_res, "Cenários A-D: 6 métodos fixos vs ordenar  (x vermelho = contagem se recusou)")
    ax[0][0].set_ylim(top=ax[0][0].get_ylim()[1] * 4)
    handles, rotulos = ax[0][0].get_legend_handles_labels()
    fig.legend(handles, rotulos, loc="lower center", ncol=len(series), fontsize=9, frameon=False)
    barras(ax[0][1], extras_res, "Cenários em que o escolher pode errar (E, F)")
    ax[0][1].set_ylim(top=ax[0][1].get_ylim()[1] * 60)
    for j, (nome, r) in enumerate(extras_res.items()):
        melhor, _ = melhor_fixo(r)
        ax[0][1].annotate(f"escolheu {r['escolha']}\nmelhor: {melhor}", (j, 1.0),
                          xycoords=("data", "axes fraction"), ha="center", va="top", fontsize=8)

    a = ax[1][0]
    for tipo, cor in (("chaves_grandes", "#2ca25f"), ("faixa_estreita", "#4393c3")):
        pts = [(l["n"], l["custo_pct"]) for l in custo if l["tipo_de_dados"] == tipo]
        a.plot(*zip(*pts), marker="o", color=cor, label=tipo)
    a.set_xscale("log")
    a.set_xlabel("n (tamanho da lista)")
    a.set_ylabel("custo do escolher / tempo de ordenar (%)")
    a.set_title("Quanto custa olhar a lista?", fontsize=10)
    a.grid(alpha=0.3)
    a.legend(fontsize=8)

    a = ax[1][1]
    ms = sorted(piores, key=piores.get)
    a.barh(ms, [piores[m] for m in ms], color=[cores[m] for m in ms])
    a.set_xscale("log")
    a.set_xlabel("pior caso (método ÷ melhor fixo do cenário), cenários A-D, escala log")
    a.set_title("Nenhum método fixo é bom nos 4 cenários; ordenar é", fontsize=10)
    for i, m in enumerate(ms):
        a.text(piores[m] * 1.08, i, f"{piores[m]:.2f}x", va="center", fontsize=8)
    a.grid(axis="x", alpha=0.3)

    fig.suptitle("Ordenação adaptativa: escolher(v) / ordenar(v)", fontsize=13)
    fig.tight_layout(rect=(0, 0.04, 1, 0.97))
    fig.savefig(caminho, dpi=130)
    plt.close(fig)
    return True


# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=20000, help="tamanho das listas dos cenários A, B, C, E, F")
    ap.add_argument("--semente", type=int, default=2024)
    ap.add_argument("--saida", default="relatorios", help="pasta de saída")
    ap.add_argument("--rapido", action="store_true", help="n=3000 e menos repetições (teste rápido)")
    ap.add_argument("--excel", action="store_true", help="CSV com ';' e vírgula decimal (Excel pt-BR)")
    ap.add_argument("--sem-grafico", action="store_true")
    args = ap.parse_args(argv)

    n, rep = (3000, 3) if args.rapido else (args.n, 9)
    tamanhos = (100, 1000, 3000) if args.rapido else (100, 1000, 10_000, 100_000)
    os.makedirs(args.saida, exist_ok=True)
    t0 = time.time()
    caminho = lambda nome: os.path.join(args.saida, nome)          # noqa: E731

    print("[1/5] testes de borda...")
    borda, falhas = testes_de_borda()
    escrever_csv(caminho("01_testes_borda.csv"),
                 ["caso", "n", "metodo", "resultado", "escolher_escolheu"], borda, args.excel)

    print(f"[2/5] cenários (n={n}, semente={args.semente})...")
    principais, extras = cenarios(n, args.semente)
    res_p, res_e = {}, {}
    for nome, v in principais.items():
        print("   ", nome, flush=True)
        res_p[nome] = medir_cenario(v, rep)
    for nome, v in extras.items():
        print("   ", nome, flush=True)
        res_e[nome] = medir_cenario(v, rep)

    campos_tab = ["cenario", "n", "insercao_ms", "intercalacao_ms", "rapida_ms", "hibrida_ms",
                  "contagem_ms", "base_ms", "ordenar_ms", "sorted_referencia_ms", "vencedor_fixo",
                  "escolher_escolheu", "ordenar_sobre_melhor", "escolher_ms", "escolher_sobre_ordenar_pct"]
    todos_v = dict(principais, **extras)
    tabela = [linha_cenario(nome, todos_v[nome], r) for nome, r in {**res_p, **res_e}.items()]
    escrever_csv(caminho("02_tabela_cenarios.csv"), campos_tab, tabela, args.excel)

    venc = []
    for nome, r in res_p.items():
        v_nome, tv = melhor_fixo(r)
        venc.append({"cenario": nome, "vencedor": v_nome, "tempo_ms": tv * 1e3,
                     "escolher_escolheu": r["escolha"],
                     "escolher_acertou": ("sim" if (r["escolha"] == v_nome or r["t"]["ordenar"] / tv < LIMIAR_ERRO)
                                             else "NAO"),
                     "por_que": por_que(v_nome, principais[nome])})
    escrever_csv(caminho("03_vencedores.csv"),
                 ["cenario", "vencedor", "tempo_ms", "escolher_escolheu", "escolher_acertou", "por_que"],
                 venc, args.excel)

    escrever_csv(caminho("04_regras_escolher.csv"),
                 ["ordem", "regra", "limiar", "origem", "tipo_da_origem"], regras(), args.excel)

    print("[3/5] custo do escolher...")
    custo = varrer_custo(tamanhos, args.semente, rep)
    escrever_csv(caminho("05_custo_escolher.csv"),
                 ["tipo_de_dados", "n", "escolheu", "min_max_ms", "escolher_ms", "ordenar_ms",
                  "custo_pct", "ns_por_elemento"], custo, args.excel)

    print("[4/5] cenários de erro e pior caso...")
    erros = linhas_erro(res_e, res_p)
    escrever_csv(caminho("06_cenario_de_erro.csv"),
                 ["cenario", "escolheu", "melhor_fixo", "tempo_do_escolhido_ms", "tempo_do_melhor_ms",
                  "ordenar_ms", "perda_x", "errou", "por_que"], erros, args.excel)
    letras = [nome[0] for nome in res_p]
    linhas_pc, piores = pior_caso(res_p)
    escrever_csv(caminho("07_pior_caso_relativo.csv"),
                 ["metodo"] + [f"cenario_{l}" for l in letras] + ["pior_caso_x", "recusou_em_algum_cenario"],
                 linhas_pc, args.excel)

    if not args.sem_grafico:
        print("[5/5] gráfico...")
        if desenhar(res_p, res_e, custo, piores, caminho("relatorio.png")):
            print("    ->", caminho("relatorio.png"))

    # ------------------------------------------------------------------ resumo
    print("\n=== RESUMO ===")
    print(f"Testes de borda: {len(borda) - falhas}/{len(borda)} OK", "" if not falhas else f"  ({falhas} FALHAS)")
    for l in venc:
        print(f"  {l['cenario']:<40} vence: {l['vencedor']:<13} escolheu: {l['escolher_escolheu']:<13} "
              f"acertou: {l['escolher_acertou']}")
    fixos_validos = {m: x for m, x in piores.items() if m != "ordenar"}
    melhor_unico = min(fixos_validos, key=fixos_validos.get)
    compensa = piores["ordenar"] * 2 < fixos_validos[melhor_unico]
    print(f"Compensa? {'SIM' if compensa else 'NAO'}: pior caso de ordenar = {piores['ordenar']:.2f}x; "
          f"do melhor método fixo único ({melhor_unico}) = {fixos_validos[melhor_unico]:.1f}x")
    caro = max(custo, key=lambda l: l["custo_pct"])
    grandes = [l["ns_por_elemento"] for l in custo if l["n"] >= 1000] or [l["ns_por_elemento"] for l in custo]
    grandes.sort()
    print(f"Custo do escolher: ~{grandes[len(grandes) // 2]:.0f} ns/elemento; no pior caso medido "
          f"{caro['custo_pct']:.0f}% do tempo de ordenar ({caro['tipo_de_dados']}, n={caro['n']})")
    for l in erros:
        if l["errou"] == "SIM":
            print(f"Erro do escolher: {l['cenario']} -> escolheu {l['escolheu']}, melhor {l['melhor_fixo']} "
                  f"({l['perda_x']:.2f}x pior)")
    print(f"Arquivos em: {os.path.abspath(args.saida)}   (total {time.time() - t0:.0f}s)")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
