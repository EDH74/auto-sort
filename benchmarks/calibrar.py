"""Calibração dos limiares do `escolher`.

Cada tabela aqui responde a uma pergunta que vira uma regra em
ordenacao/escolhedor.py. Rodar:  python -m benchmarks.calibrar
Semente fixa: as mesmas listas em toda execução.
"""
import random

from ordenacao import metodos as m
from ordenacao.escolhedor import _descidas_na_amostra
from benchmarks._tempo import medir

SEMENTE = 12345


def ms(t):
    return f"{t * 1e3:9.3f}"


def lista_aleatoria(n, lo, hi, rng):
    return [rng.randint(lo, hi) for _ in range(n)]


def q1_corte_hibrida():
    print("\n[1] Corte da híbrida (n=20000, aleatória, ms)")
    rng = random.Random(SEMENTE)
    v = lista_aleatoria(20000, -2**31, 2**31, rng)
    for corte in (1, 8, 16, 24, 32, 48, 64):
        def f(corte=corte):
            a = list(v)
            m._quick(a, 0, len(a), corte)
        print(f"  corte={corte:3d}: {ms(medir(f, repeticoes=3))}")


def q2_insercao_vs_hibrida():
    print("\n[2] Lista pequena: inserção vs híbrida vs intercalação (µs/chamada)")
    rng = random.Random(SEMENTE)
    print("     n    insercao   hibrida  intercalacao")
    for n in (8, 16, 24, 32, 48, 64, 96, 128, 256):
        v = lista_aleatoria(n, -2**31, 2**31, rng)
        t = [medir(m.METODOS[k], v) * 1e6 for k in ("insercao", "hibrida", "intercalacao")]
        print(f"  {n:4d}  {t[0]:9.1f} {t[1]:9.1f} {t[2]:9.1f}")


def q3_contagem_vs_base():
    print("\n[3] Contagem vs base vs híbrida conforme k/n (n=50000, ms)")
    rng = random.Random(SEMENTE)
    n = 50000
    print("   k/n        k   contagem      base   hibrida")
    for razao in (0.1, 1, 2, 4, 8, 16, 64, 256):
        k = max(2, int(n * razao))
        v = lista_aleatoria(n, 0, k - 1, rng)
        try:
            tc = medir(m.contagem, v, repeticoes=3)
        except m.FaixaGrandeDemais:
            tc = float("nan")          # a contagem se recusou: faixa grande demais
        tb = medir(m.base, v, repeticoes=3)
        th = medir(m.hibrida, v, repeticoes=3)
        print(f"  {razao:5}  {k:8d} {ms(tc)} {ms(tb)} {ms(th)}")


def q4_base_vs_hibrida():
    print("\n[4] Base vs híbrida por tamanho e largura da chave (ms)")
    rng = random.Random(SEMENTE)
    print("       n  bits   passadas      base   hibrida  intercalacao")
    for n in (200, 1000, 5000, 20000, 100000):
        for bits in (16, 32, 48):
            v = lista_aleatoria(n, 0, 2**bits - 1, rng)
            tb = medir(m.base, v, repeticoes=3)
            th = medir(m.hibrida, v, repeticoes=3)
            ti = medir(m.intercalacao, v, repeticoes=3)
            print(f"  {n:6d}  {bits:4d}  {bits // 8:8d} {ms(tb)} {ms(th)} {ms(ti)}")


def q5_quase_ordenado():
    print("\n[5] Quase ordenado, n=20000, chaves grandes (ms)")
    rng = random.Random(SEMENTE)
    n = 20000
    base_ord = sorted(lista_aleatoria(n, -2**31, 2**31, rng))
    print("  %trocas  descidas/256  insercao  intercalacao  hibrida     base")
    for pct in (0, 0.1, 0.5, 1, 2, 5, 10):
        v = list(base_ord)
        for _ in range(int(n * pct / 100)):
            i, j = rng.randrange(n), rng.randrange(n)
            v[i], v[j] = v[j], v[i]
        d = _descidas_na_amostra(v)[0]
        print(f"  {pct:6}  {d:10d} "
              f"{ms(medir(m.insercao, v, repeticoes=3))}"
              f" {ms(medir(m.intercalacao, v, repeticoes=3))}"
              f" {ms(medir(m.hibrida, v, repeticoes=3))}"
              f" {ms(medir(m.base, v, repeticoes=3))}")


if __name__ == "__main__":
    q1_corte_hibrida()
    q2_insercao_vs_hibrida()
    q3_contagem_vs_base()
    q4_base_vs_hibrida()
    q5_quase_ordenado()
