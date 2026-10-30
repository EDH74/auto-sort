"""Os seis métodos de ordenação do semestre.

Todos recebem uma lista de inteiros e DEVOLVEM uma lista nova ordenada
(a entrada não é modificada). Isso deixa os testes e as medições simples.
"""
import random

# Tamanho de partição abaixo do qual a rápida híbrida troca para inserção.
CORTE_HIBRIDA = 32

# Trava de segurança da contagem: número máximo de posições do vetor de
# contagem. 10 milhões de posições ~ 80 MB só de ponteiros. Acima disso a
# contagem recusa em vez de estourar a memória.
LIMITE_FAIXA_CONTAGEM = 10_000_000


class FaixaGrandeDemais(MemoryError):
    """A faixa de valores é grande demais para a ordenação por contagem."""


# --------------------------------------------------------------------------
# 1. Inserção
# --------------------------------------------------------------------------
def _insercao_intervalo(a, lo, hi):
    """Ordena a[lo:hi] in-place por inserção."""
    for i in range(lo + 1, hi):
        x = a[i]
        j = i - 1
        while j >= lo and a[j] > x:
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = x


def insercao(v):
    a = list(v)
    _insercao_intervalo(a, 0, len(a))
    return a


# --------------------------------------------------------------------------
# 2. Intercalação (merge sort top-down, estável)
#    Otimização clássica: se a[mid-1] <= a[mid] as duas metades já formam
#    uma sequência ordenada e a intercalação é pulada.
# --------------------------------------------------------------------------
def _ms(a, aux, lo, hi):
    if hi - lo < 2:
        return
    mid = (lo + hi) // 2
    _ms(a, aux, lo, mid)
    _ms(a, aux, mid, hi)
    if a[mid - 1] <= a[mid]:
        return
    aux[lo:hi] = a[lo:hi]
    i, j = lo, mid
    for k in range(lo, hi):
        if i >= mid:
            a[k] = aux[j]
            j += 1
        elif j >= hi:
            a[k] = aux[i]
            i += 1
        elif aux[j] < aux[i]:
            a[k] = aux[j]
            j += 1
        else:
            a[k] = aux[i]
            i += 1


def intercalacao(v):
    a = list(v)
    if len(a) > 1:
        _ms(a, a[:], 0, len(a))
    return a


# --------------------------------------------------------------------------
# 3 e 4. Rápida com pivô aleatório (partição em 3 vias, para lidar bem com
#    chaves repetidas) e rápida híbrida (corta para inserção em partições
#    pequenas). As duas compartilham o mesmo código; muda só o corte.
# --------------------------------------------------------------------------
def _quick(a, lo, hi, corte):
    # Recursão só no lado menor; o lado maior vira laço -> profundidade O(log n).
    while hi - lo > corte:
        p = a[random.randrange(lo, hi)]
        lt, i, gt = lo, lo, hi
        while i < gt:
            x = a[i]
            if x < p:
                a[i] = a[lt]
                a[lt] = x
                lt += 1
                i += 1
            elif x > p:
                gt -= 1
                a[i] = a[gt]
                a[gt] = x
            else:
                i += 1
        if lt - lo < hi - gt:
            _quick(a, lo, lt, corte)
            lo = gt
        else:
            _quick(a, gt, hi, corte)
            hi = lt
    if corte > 1 and hi - lo > 1:
        _insercao_intervalo(a, lo, hi)


def rapida(v):
    a = list(v)
    _quick(a, 0, len(a), 1)
    return a


def hibrida(v):
    a = list(v)
    _quick(a, 0, len(a), CORTE_HIBRIDA)
    return a


# --------------------------------------------------------------------------
# 5. Contagem (inteiros; aceita negativos deslocando pelo mínimo)
# --------------------------------------------------------------------------
def contagem(v, minimo=None, maximo=None):
    """`minimo`/`maximo` opcionais evitam reler a lista quando quem chama
    (o `escolher`) já os conhece."""
    if not v:
        return []
    lo = min(v) if minimo is None else minimo
    hi = max(v) if maximo is None else maximo
    k = hi - lo + 1
    if k > LIMITE_FAIXA_CONTAGEM:
        raise FaixaGrandeDemais(
            f"faixa de {k} valores > limite de {LIMITE_FAIXA_CONTAGEM}")
    cont = [0] * k
    for x in v:
        cont[x - lo] += 1
    saida = []
    for idx, c in enumerate(cont):
        if c:
            saida.extend([idx + lo] * c)
    return saida


# --------------------------------------------------------------------------
# 6. Base (radix sort LSD, base 256; negativos tratados deslocando pelo mínimo)
# --------------------------------------------------------------------------
def base(v, minimo=None, maximo=None):
    if not v:
        return []
    lo = min(v) if minimo is None else minimo
    hi = max(v) if maximo is None else maximo
    if lo == hi:
        return list(v)
    chaves = [x - lo for x in v]          # agora todas >= 0
    passadas = ((hi - lo).bit_length() + 7) // 8
    for p in range(passadas):
        shift = 8 * p
        baldes = [[] for _ in range(256)]
        for x in chaves:
            baldes[(x >> shift) & 255].append(x)
        chaves = [x for b in baldes for x in b]
    return [x + lo for x in chaves]


METODOS = {
    "insercao": insercao,
    "intercalacao": intercalacao,
    "rapida": rapida,
    "hibrida": hibrida,
    "contagem": contagem,
    "base": base,
}
