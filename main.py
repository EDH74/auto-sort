"""
Gera testes, uma planilha CSV e um gráfico JPEG para o projeto de ordenação.
"""
#from __future__ import annotations

import argparse
import csv
import random
import statistics
import subprocess
import sys
import time
from pathlib import Path

from ordenacao import METODOS, FaixaGrandeDemais, ordenar, escolher

METODOS_FIXOS = [
    "insercao", "intercalacao", "rapida",
    "hibrida", "contagem", "base",
]
METODOS_MEDIDOS = METODOS_FIXOS + ["ordenar"]


def criar_cenarios(n: int, semente: int):
    """Cria as quatro entradas principais, com semente reproduzível."""
    rng = random.Random(semente)

    aleatoria_grande = [
        rng.randint(-(2**31), 2**31) for _ in range(n)
    ]
    faixa_estreita = [rng.randint(-500, 500) for _ in range(n)]

    quase_ordenada = sorted(
        rng.randint(-(2**31), 2**31) for _ in range(n)
    )
    quantidade_trocas = max(1, int(n * 0.01)) if n > 1 else 0
    for _ in range(quantidade_trocas):
        i = rng.randrange(n)
        j = rng.randrange(n)
        quase_ordenada[i], quase_ordenada[j] = (
            quase_ordenada[j], quase_ordenada[i]
        )

    minuscula = [rng.randint(-10**6, 10**6) for _ in range(16)]

    return {
        "Aleatório com chaves grandes": aleatoria_grande,
        "Faixa estreita (-500 a 500)": faixa_estreita,
        "Quase ordenado (1% de trocas)": quase_ordenada,
        "Lista minúscula (16 elementos)": minuscula,
    }


def executar_testes():
    """Executa os testes automatizados que já existem no repositório."""
    print("\n[1/3] Executando testes automatizados...")
    resultado = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        check=False,
    )
    if resultado.returncode != 0:
        raise SystemExit(
            "\nOs testes falharam. Corrija os erros antes de gerar os resultados."
        )
    print("Todos os testes passaram.")


def medir_mediana(funcao, entrada, repeticoes):
    """Mede a função em cópias idênticas e retorna a mediana em segundos."""
    tempos = []
    esperado = sorted(entrada)

    for _ in range(repeticoes):
        copia = list(entrada)
        inicio = time.perf_counter()
        resultado = funcao(copia)
        fim = time.perf_counter()

        if resultado != esperado:
            raise AssertionError(
                f"{getattr(funcao, '__name__', funcao)} produziu resultado incorreto"
            )
        tempos.append(fim - inicio)

    return statistics.median(tempos)


def medir_cenario(nome_cenario, entrada, repeticoes):
    """Mede os seis métodos fixos e o ordenador adaptativo."""
    resultados = []
    print(f"\nMedindo: {nome_cenario} (n={len(entrada):,})")

    for nome in METODOS_MEDIDOS:
        funcao = ordenar if nome == "ordenar" else METODOS[nome]
        try:
            tempo = medir_mediana(funcao, entrada, repeticoes)
            status = "OK"
            tempo_ms = tempo * 1000
            print(f"  {nome:14s}: {tempo_ms:10.4f} ms")
        except FaixaGrandeDemais:
            tempo_ms = None
            status = "Recusado: faixa grande"
            print(f"  {nome:14s}: recusado (faixa grande demais)")

        resultados.append({
            "cenario": nome_cenario,
            "tamanho": len(entrada),
            "metodo": nome,
            "tempo_mediano_ms": tempo_ms,
            "status": status,
        })

    # O seletor retorna o nome do algoritmo, não uma lista ordenada;
    # por isso sua medição não pode usar a validação de saída acima.
    tempos_escolher = []
    for _ in range(repeticoes):
        inicio = time.perf_counter()
        escolher(list(entrada))
        tempos_escolher.append(time.perf_counter() - inicio)
    tempo_escolher = statistics.median(tempos_escolher) * 1000
    resultados.append({
        "cenario": nome_cenario,
        "tamanho": len(entrada),
        "metodo": "escolher (isolado)",
        "tempo_mediano_ms": tempo_escolher,
        "status": "OK",
    })
    print(f"  {'escolher (isolado)':14s}: {tempo_escolher:10.4f} ms")

    return resultados


def salvar_csv(linhas, caminho):
    colunas = [
        "cenario", "tamanho", "metodo",
        "tempo_mediano_ms", "status",
    ]
    with caminho.open("w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas)
        escritor.writeheader()
        escritor.writerows(linhas)


def salvar_grafico(linhas, caminho):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise SystemExit(
            "\nA biblioteca matplotlib não está instalada.\n"
            "Instale com: python -m pip install matplotlib"
        )

    cenarios = list(dict.fromkeys(l["cenario"] for l in linhas))
    metodos = METODOS_MEDIDOS
    fig, ax = plt.subplots(figsize=(14, 7))

    largura = 0.11
    posicoes = list(range(len(cenarios)))

    for indice, metodo in enumerate(metodos):
        valores = []
        for cenario in cenarios:
            linha = next(
                (l for l in linhas
                 if l["cenario"] == cenario and l["metodo"] == metodo),
                None,
            )
            valores.append(
                linha["tempo_mediano_ms"]
                if linha and linha["tempo_mediano_ms"] is not None
                else 0
            )

        deslocamento = (indice - (len(metodos) - 1) / 2) * largura
        barras = ax.bar(
            [p + deslocamento for p in posicoes],
            valores,
            largura,
            label=metodo,
        )
        # Marca visualmente os métodos recusados/sem medição.
        for barra, valor in zip(barras, valores):
            if valor == 0:
                barra.set_alpha(0.15)

    ax.set_title("Desempenho dos algoritmos de ordenação")
    ax.set_xlabel("Cenário de teste")
    ax.set_ylabel("Tempo mediano (milissegundos)")
    ax.set_xticks(posicoes)
    ax.set_xticklabels(cenarios, rotation=12, ha="right")
    ax.set_yscale("log")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(title="Método", ncols=4, fontsize=8)
    fig.tight_layout()
    fig.savefig(caminho, format="jpeg", dpi=180, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(
        description="Executa testes e gera CSV/JPEG dos algoritmos."
    )
    parser.add_argument(
        "--n", type=int, default=3000,
        help="Quantidade de elementos nos três cenários grandes (padrão: 3000).",
    )
    parser.add_argument(
        "--repeticoes", type=int, default=5,
        help="Número de repetições por método (padrão: 5).",
    )
    parser.add_argument(
        "--semente", type=int, default=2024,
        help="Semente para reproduzir as mesmas listas (padrão: 2024).",
    )
    args = parser.parse_args()

    if args.n < 1 or args.repeticoes < 1:
        parser.error("--n e --repeticoes precisam ser maiores que zero.")

    raiz = Path(__file__).resolve().parent
    # Garante que imports e testes sejam executados a partir da raiz do projeto.
    import os
    os.chdir(raiz)

    executar_testes()

    print("\n[2/3] Criando cenários e medindo os métodos...")
    cenarios = criar_cenarios(args.n, args.semente)
    linhas = []
    for nome, entrada in cenarios.items():
        linhas.extend(medir_cenario(nome, entrada, args.repeticoes))

    print("\n[3/3] Salvando arquivos...")
    csv_path = raiz / "resultados_ordenacao.csv"
    jpg_path = raiz / "grafico_ordenacao.jpg"
    salvar_csv(linhas, csv_path)
    salvar_grafico(linhas, jpg_path)

    print("\nConcluído!")
    print(f"CSV:    {csv_path}")
    print(f"Gráfico: {jpg_path}")
    print("\nObservação: o eixo vertical do gráfico é logarítmico para")
    print("permitir comparar métodos com tempos muito diferentes.")


if __name__ == "__main__":
    main()
