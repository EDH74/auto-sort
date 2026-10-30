# Resultados (tempo mediano de uma chamada, em ms)

n = 20000 nos cenários A, B, C, E, F; semente 2024. Em negrito, o mais rápido entre os seis métodos fixos.

## Cenários principais

| cenário | insercao | intercalacao | rapida | hibrida | contagem | base | ordenar | sorted() (ref.) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A. aleatório, chaves grandes | 5267.9 | 27.2 | 29.4 | 25.7 | recusa (faixa) | **6.7** | 7.2 | 3.6 |
| B. faixa estreita [-500, 500] | 5029.0 | 26.4 | 17.0 | 18.3 | **1.5** | 3.7 | 1.5 | 2.5 |
| C. quase ordenado (1% de trocas) | 138.2 | 15.1 | 28.3 | 25.4 | recusa (faixa) | **6.3** | 6.7 | 0.4729 |
| D. lista minúscula (n=16) | 0.0034 | 0.0062 | 0.0070 | **0.0034** | 39.9 | 0.0460 | 0.0034 | 0.0003 |

### Decisão do `escolher` e custo

| cenário | escolheu | melhor fixo | ordenar ÷ melhor | escolher (ms) | escolher ÷ ordenar |
|---|---|---|---:|---:|---:|
| A. aleatório, chaves grandes | base | base | 1.08× | 0.7382 | 10.2% |
| B. faixa estreita [-500, 500] | contagem | contagem | 1.01× | 0.5156 | 33.7% |
| C. quase ordenado (1% de trocas) | base | base | 1.05× | 0.3883 | 5.8% |
| D. lista minúscula (n=16) | insercao | hibrida | 1.01× | 0.0001 | 2.1% |

## Cenários extras (onde o `escolher` pode errar)

| cenário | insercao | intercalacao | rapida | hibrida | contagem | base | ordenar | sorted() (ref.) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| E. 5 chaves distintas em faixa de 2^32 | 4148.1 | 24.1 | 3.4 | **3.4** | recusa (faixa) | 5.9 | 6.5 | 1.5 |
| F. quase ordenado (0,3% de trocas) | 43.7 | 14.4 | 27.4 | 30.0 | recusa (faixa) | **8.4** | 6.6 | 0.2881 |

| cenário | escolheu | melhor fixo | ordenar ÷ melhor | escolher (ms) | escolher ÷ ordenar |
|---|---|---|---:|---:|---:|
| E. 5 chaves distintas em faixa de 2^32 | base | hibrida | 1.95× | 0.4911 | 7.5% |
| F. quase ordenado (0,3% de trocas) | base | base | 0.79× | 0.3480 | 5.3% |
