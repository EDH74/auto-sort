"""`escolher(v)` e `ordenar(v)`.

Cada limiar abaixo vem de uma tabela de `python -m benchmarks.calibrar`
(o número da tabela está no comentário). Resultados em RELATORIO.md.

Custo do olhar: `min` e `max` são duas passadas, mas em C (~25 ns por
elemento no total); a ordem é checada só por AMOSTRA de pares (~256
comparações), nunca percorrendo a lista inteira em Python. Medido em
benchmarks/custo_escolher.py: ~5-8% do tempo de `ordenar` no caso geral e
até ~35-50% quando a contagem é escolhida (ela é tão rápida que olhar pesa).
"""
from .metodos import METODOS, hibrida

# --- limiares (de onde vieram) -------------------------------------------
N_MINUSCULA = 32            # [2] até ~32 a inserção empata ou ganha da híbrida,
                            #     e dispensa qualquer olhada na lista
N_MIN_BASE = 512            # [4] base perde em n=200 (4+ passadas) e ganha 1,5-4x
                            #     em n>=1000; o cruzamento está entre os dois
MAX_PASSADAS_BASE = 6       # [4] medido até 6 passadas (chaves de 48 bits)
RAZAO_CONTAGEM = 4          # [3] contagem ganha ou empata até k/n = 4;
                            #     a partir de k/n = 8 a base é mais rápida
FAIXA_MAX_CONTAGEM = 4_000_000   # trava de memória: ~8 bytes/posição = ~32 MB
AMOSTRA = 256               # pares adjacentes inspecionados (era 64: a amostra
                            # pequena deixou passar 1% de trocas, ver RELATORIO)
# [5] sem nenhuma descida na amostra -> intercalação (com atalho "metades
#     já ordenadas" é O(n) em dado ordenado e só ~2x pior que a base se a
#     amostra enganar). Inserção seria mais rápida em dado 100% ordenado,
#     mas até 11x pior se a amostra enganar, por isso não é usada aqui.


def _descidas_na_amostra(v):
    """(descidas, pares) em ~AMOSTRA pares adjacentes igualmente espaçados."""
    n = len(v)
    passo = max(1, (n - 1) // AMOSTRA)
    pos = range(0, n - 1, passo)
    return sum(1 for i in pos if v[i] > v[i + 1]), len(pos)


def _so_inteiros_na_amostra(v):
    n = len(v)
    passo = max(1, n // AMOSTRA)
    return all(type(v[i]) is int for i in range(0, n, passo))


def _planejar(v):
    """Devolve (nome_do_método, minimo, maximo); min/max None se não lidos."""
    n = len(v)
    if n <= N_MINUSCULA:
        return "insercao", None, None

    if not _so_inteiros_na_amostra(v):
        return "hibrida", None, None          # contagem/base exigem inteiros

    lo, hi = min(v), max(v)                   # 2 passadas em C
    k = hi - lo + 1                           # tamanho que a contagem alocaria

    # Previsão de memória ANTES de chamar a contagem.
    if k <= RAZAO_CONTAGEM * n and k <= FAIXA_MAX_CONTAGEM:
        return "contagem", lo, hi

    descidas, _ = _descidas_na_amostra(v)
    if descidas == 0:
        return "intercalacao", lo, hi

    passadas = ((hi - lo).bit_length() + 7) // 8
    if n >= N_MIN_BASE and passadas <= MAX_PASSADAS_BASE:
        return "base", lo, hi

    return "hibrida", lo, hi


def escolher(v):
    """Nome do método mais adequado para ordenar `v`."""
    return _planejar(v)[0]


def ordenar(v):
    """Escolhe e executa. Devolve uma lista nova, ordenada."""
    nome, lo, hi = _planejar(v)
    try:
        if nome == "contagem" or nome == "base":
            return METODOS[nome](v, lo, hi)
        return METODOS[nome](v)
    except TypeError:
        # um elemento não-inteiro fora da amostra: caminho genérico
        return hibrida(v)
