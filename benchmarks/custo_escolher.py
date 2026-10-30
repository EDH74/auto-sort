"""Quanto custa olhar a lista? Decompõe o `escolher` por tamanho.

Uso: python -m benchmarks.custo_escolher
"""
import random
import sys

from ordenacao import ordenar, escolher
from ordenacao.escolhedor import _descidas_na_amostra, _so_inteiros_na_amostra
from benchmarks._tempo import medir


def main():
    rng = random.Random(99)
    print("Aleatório com chaves grandes (o caso em que o escolher decide 'base').")
    print("Tempos em ms; 'olhar' = escolher completo.\n")
    print(f"{'n':>8} {'min+max':>9} {'amostras':>9} {'olhar':>9} {'ordenar':>9} {'olhar/ordenar':>14}")
    for n in (100, 1000, 10_000, 100_000, 400_000):
        v = [rng.randint(-2**31, 2**31) for _ in range(n)]
        t_mm = medir(lambda: (min(v), max(v)))
        t_am = medir(lambda: (_descidas_na_amostra(v), _so_inteiros_na_amostra(v)))
        t_es = medir(escolher, v)
        t_or = medir(ordenar, v, repeticoes=3)
        print(f"{n:8d} {t_mm*1e3:9.4f} {t_am*1e3:9.4f} {t_es*1e3:9.4f} "
              f"{t_or*1e3:9.2f} {t_es/t_or:13.1%}")

    print("\nFaixa estreita (o caso em que o olhar pesa mais: a contagem é rápida).")
    print(f"{'n':>8} {'olhar':>9} {'ordenar':>9} {'olhar/ordenar':>14}")
    for n in (1000, 10_000, 100_000, 400_000):
        v = [rng.randint(-500, 500) for _ in range(n)]
        t_es = medir(escolher, v)
        t_or = medir(ordenar, v, repeticoes=3)
        print(f"{n:8d} {t_es*1e3:9.4f} {t_or*1e3:9.2f} {t_es/t_or:13.1%}")

    print("\nMemória do vetor de contagem (CPython, 8 bytes por posição):")
    for k in (10**5, 10**6, 4_000_000):
        print(f"  k={k:>9,}: {sys.getsizeof([0] * k) / 1e6:8.1f} MB")
    print("  k=4,3e9 (faixa de 32 bits com sinal): ~34 000 MB -> inviável")


if __name__ == "__main__":
    main()
