"""Cronometragem simples e reprodutível."""
import gc
import statistics
import time


def medir(fn, *args, repeticoes=5, minimo_s=0.02):
    """Tempo mediano, em segundos, de UMA chamada de fn(*args).

    Para chamadas muito curtas (listas minúsculas) repete a chamada em laço
    até somar `minimo_s` e divide, para o relógio não dominar a medida.
    """
    t0 = time.perf_counter()
    fn(*args)
    unit = time.perf_counter() - t0
    laco = max(1, int(minimo_s / unit)) if unit > 0 else 1000
    if unit > 0.5:                       # chamadas de segundos: 3 repetições bastam
        repeticoes = min(repeticoes, 3)
    amostras = []
    gc.disable()
    try:
        for _ in range(repeticoes):
            t0 = time.perf_counter()
            for _ in range(laco):
                fn(*args)
            amostras.append((time.perf_counter() - t0) / laco)
    finally:
        gc.enable()
    return statistics.median(amostras)
