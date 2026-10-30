# Relatório — ordenação adaptativa (`escolher` / `ordenar`)

Todos os números abaixo foram medidos por `python -m benchmarks.medir`,
`benchmarks.calibrar` e `benchmarks.custo_escolher` e estão salvos em
`benchmarks/` (`resultados.md/json`, `calibracao.txt`, `custo_escolher.txt`).

**Ambiente das medições:** Python 3.12.3, Linux, 1 núcleo de CPU compartilhado
(o sandbox em que o código foi gerado, não um servidor dedicado nem a máquina de vocês).
Listas de inteiros, `n = 20 000` (cenários A, B, C, E, F), `n = 16` (D),
semente 2024, mediana de 9 repetições (3 para chamadas de vários segundos),
coletor de lixo desligado durante a medida. Todos os métodos devolvem uma
cópia ordenada, então todos pagam a mesma cópia.

> **Ruído:** repetindo as medições, os mesmos métodos variam em torno de
> ±20–30%. Quando `ordenar` aparece 0,8× ou 1,08× de um método que ele
> executa por dentro, isso é ruído, não ganho nem perda. Só diferenças de
> 2× ou mais são conclusões. **Refaçam as medições na máquina de vocês e
> troquem as tabelas** (README, seção "Como refazer").

---

## 1. Tabela: quatro cenários × seis métodos (+ `ordenar`)

Tempo de uma chamada, em **ms**. Negrito = mais rápido entre os seis métodos fixos.
`recusa` = a contagem se recusou a rodar porque a faixa de valores exigiria um vetor
de contagem gigante (ver §4). `sorted()` do Python (em C) aparece só como referência
e não é um dos seis métodos.

| cenário | inserção | intercalação | rápida | híbrida | contagem | base | **ordenar** | `sorted()` (ref.) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A. aleatório, chaves grandes (±2³¹) | 5267,9 | 27,2 | 29,4 | 25,7 | recusa | **6,7** | 7,2 | 3,6 |
| B. faixa estreita [−500, 500] | 5029,0 | 26,4 | 17,0 | 18,3 | **1,5** | 3,7 | 1,5 | 2,5 |
| C. quase ordenado (1% de trocas, chaves grandes) | 138,2 | 15,1 | 28,3 | 25,4 | recusa | **6,3** | 6,7 | 0,47 |
| D. lista minúscula (n = 16) | 0,0034 | 0,0062 | 0,0070 | **0,0034** | 39,9 | 0,0460 | 0,0034 | 0,0003 |

O que `ordenar` escolheu, e o que custou olhar a lista:

| cenário | escolheu | melhor fixo | ordenar ÷ melhor | `escolher` (ms) | `escolher` ÷ `ordenar` |
|---|---|---|---:|---:|---:|
| A | base | base | 1,08× | 0,738 | 10,2% |
| B | contagem | contagem | 1,01× | 0,516 | 33,7% |
| C | base | base | 1,05× | 0,388 | 5,8% |
| D | inserção | híbrida (empate) | 1,01× | 0,0001 | 2,1% |

## 2. Quem venceu cada cenário, e por quê

**A — aleatório com chaves grandes: base (6,7 ms).** Chaves de 32 bits exigem 4
passadas lineares de base 256; as comparações dos métodos baseados em comparação
custam ~15 níveis de `n log n`, cada comparação em Python puro. Base ficou ~4× à
frente de intercalação/rápida/híbrida. A contagem não pôde rodar: a faixa tem ≈ 4,3
bilhões de valores e o vetor de contagem teria ≈ 34 GB (§4).

**B — faixa estreita: contagem (1,5 ms).** São 1001 valores possíveis para 20 000
elementos; custo O(n + k) com k pequeno. Base foi 2,4× mais lenta (paga 2
passadas com 256 baldes) e a família de comparações, 11–17× mais lenta. Inserção
fez ~10⁸ deslocamentos (≈5 s).

**C — quase ordenado: base (6,3 ms).** Resultado que contraria a intuição: "quase
ordenado" **não** deu vitória à inserção. Com 1% de trocas de pares aleatórios (200
trocas), cada troca joga um elemento a ~n/3 posições de distância, o que gera
cerca de 2 milhões de inversões no total; a inserção, que paga uma por inversão, ficou 22×
atrás. Intercalação com atalho de "metades já ordenadas" foi bem (2,4×), mas a
base ignora a ordem e custa o mesmo que em A. A inserção só ganha em dado
praticamente 100% ordenado (calibração [5]: 1,4 ms ordenado, contra 2,9 da
intercalação e 6,1 da base).

**D — lista minúscula (16): empate técnico entre inserção e híbrida (0,0034 ms).**
Para n = 16 a híbrida cai direto na inserção (o corte é 32), então são o mesmo
código; a diferença na terceira casa é ruído. O destaque aqui é a contagem:
**39,9 ms**, ~11 800× pior, porque aloca um vetor de ~2 milhões de posições
(faixa ±10⁶) para ordenar 16 números.

### Pior caso relativo (método ÷ melhor fixo do cenário, cenários A–D)

| método | A | B | C | D | pior |
|---|---:|---:|---:|---:|---:|
| inserção | 792 | 3322 | 21,8 | 1,0 | 3322× |
| intercalação | 4,1 | 17,5 | 2,4 | 1,8 | 17,5× |
| rápida (pivô aleatório) | 4,4 | 11,2 | 4,5 | 2,1 | 11,2× |
| híbrida | 3,9 | 12,1 | 4,0 | 1,0 | 12,1× |
| contagem | recusa | 1,0 | recusa | 11 787 | falha / 11 787× |
| base | 1,0 | 2,4 | 1,0 | 13,6 | 13,6× |
| **ordenar** | 1,08 | 1,01 | 1,05 | 1,01 | **1,08×** |

Nenhum método fixo é bom nos quatro cenários. Cada um tem pelo menos um cenário
em que é de 11× a milhares de vezes pior que o melhor.

## 3. As regras do `escolher` e de onde vieram

Ordem de avaliação (código em `ordenacao/escolhedor.py`):

| # | regra | de onde veio |
|---|---|---|
| 1 | `n ≤ 32` → **inserção**, sem olhar nada | Calibração [2]: até n≈32 inserção e híbrida são iguais (a híbrida *é* inserção abaixo do corte); inserção perde de 1,3× a 4× de n=48 em diante. Não olhar a lista nesse tamanho evita o custo do `escolher`. |
| 2 | elementos amostrados não são `int` → **híbrida** | Teoria: contagem e base indexam por valor e só servem a inteiros. Híbrida compara com `<`, serve a qualquer tipo. |
| 3 | `k = máx − mín + 1`; se `k ≤ 4n` **e** `k ≤ 4 000 000` → **contagem** | `4n`: Calibração [3] (n=50 000): contagem ganha de 3× a 0,1n, empata com a base perto de `k/n = 4` e perde de `k/n = 8` em diante. `4 000 000`: **decisão de projeto**, não medida. São ~32 MB de vetor de contagem (8 bytes/posição, medido com `sys.getsizeof`), um teto que qualquer máquina aguenta; protege listas muito grandes em que `4n` ainda seria enorme. |
| 4 | **nenhuma** descida entre ~256 pares adjacentes amostrados → **intercalação** | Calibração [5]: com o atalho "se `a[mid-1] ≤ a[mid]` não intercala", a intercalação é O(n) em dado ordenado. A inserção seria ainda mais rápida em dado 100% ordenado (1,4 ms contra 2,9), mas 4× pior que a intercalação (e 13× pior que a base) se a amostra enganar (0,5% de trocas: 80 ms contra 21 ms e 6 ms), então escolhemos a opção segura. |
| 5 | `n ≥ 512` e chaves de ≤ 6 passadas (≤ 48 bits) → **base** | Calibração [4]: com n=200 a base perde (4 passadas: 0,132 contra 0,113 ms; 6: 0,199 contra 0,106); com n=1000 ganha em todas as larguras (1,4× a 4×). O ponto de virada está entre 200 e 1000; **512 é um chute dentro desse intervalo, não um ponto medido**. Seis passadas é a maior largura que testei. |
| 6 | senão → **híbrida** | Melhor método de comparação em todas as tabelas (rápida e intercalação ficam empatadas ou atrás). |

Corte da híbrida (`CORTE_HIBRIDA = 32`): a Calibração [1] não consegue distinguir
cortes de 8 a 64; três execuções dão ordens diferentes (em uma, 32 foi o melhor;
em outra, o pior). **É ruído** (o ambiente é um núcleo compartilhado). Fixei 32
porque coincide com o limite da regra 1, não porque 32 seja ótimo.

**Honestidade sobre o ajuste:** a amostra de ordem começou com 64 pares. No
cenário C ela viu 0 descidas, escolheu intercalação e perdeu 2,1× para a base.
Aumentei para 256 pares (custo: ~25–30 µs) e C passou a ser decidido corretamente.
Ou seja, **o cenário C foi usado para ajustar uma regra**, não é um teste
independente. O cenário F (0,3% de trocas, nunca usado para ajuste) também errou
com 64 pares; com 256 acertou nesta semente, mas a amostra continua
probabilística (ver §5).

## 4. Quanto custa rodar o `escolher`? Compensa?

O `escolher` faz: duas passadas em C (`min`, `max`), ~256 comparações de amostra e
uma checagem de tipo em ~256 posições. A parte cara é `min+max`: **~25 ns por elemento**, e é
inevitável, porque prever o tamanho do vetor de contagem exige a faixa exata (uma
amostra poderia subestimá-la e estourar a memória).

Medido (`benchmarks/custo_escolher.txt`, ms):

| n | aleatório, chaves grandes: `escolher` | `ordenar` | custo | faixa estreita: `escolher` | `ordenar` | custo |
|---:|---:|---:|---:|---:|---:|---:|
| 1 000 | 0,048 | 0,47 | 10,3% | 0,035 | 0,19 | 18,2% |
| 10 000 | 0,361 | 3,48 | 10,4% | 0,251 | 0,80 | 31,1% |
| 100 000 | 2,83 | 40,6 | 7,0% | 2,58 | 6,87 | 37,5% |
| 400 000 | 9,65 | 186,9 | 5,2% | 9,66 | 28,7 | 33,6% |

- **Quando as chaves são grandes** o olhar custa 5–10% do total. É barato porque
  a base é bem mais lenta que um `min`/`max` em C.
- **Quando a contagem é escolhida** o olhar custa **um terço do tempo**: a
  própria contagem é tão rápida que olhar a lista pesa quase tanto quanto
  ordenar. Esse é exatamente o aviso do enunciado, e é um custo real. Uma
  mitigação aplicada: `ordenar` repassa `mín` e `máx` à contagem/base, que não
  os recalculam (sem isso a lista seria varrida por `min`/`max` duas vezes).
- **Listas ≤ 32:** custo 0,0001 ms, nenhuma olhada.
- **Em listas curtas** o olhar pesa proporcionalmente mais: ~17% em n=100 (0,011 de 0,06 ms).

**Compensa?** Sim, pelo seguro que compra: contra o *melhor fixo de cada cenário*,
`ordenar` ficou a 1,01–1,08× (dentro do ruído); contra qualquer método fixo
**único**, o pior caso é de 11× a milhares de vezes (tabela do §2). O custo é
0,3–0,7 ms em n=20 000, 5–10% do tempo na maioria dos casos e ~34% no melhor caso
da contagem. Se o programa só ordena listas de um tipo conhecido, um método fixo
escolhido na mão ganha esses 5–34%. O `escolher` vale quando o formato dos dados
não é conhecido de antemão.

Ressalva: **todos** os métodos deste trabalho (Python puro) ficaram 2–8× atrás do
`sorted()` do Python (Timsort em C, coluna de referência). Os números absolutos e
as proporções dependem do Python: em C/Java/Rust as constantes mudam (a
base, por exemplo, ganha menos de comparações), e os limiares precisariam ser
recalibrados. O método de calibrar se mantém.

## 5. Um cenário em que o `escolher` erra a decisão

**E — poucas chaves distintas espalhadas numa faixa enorme** (5 valores distintos
sorteados em ±2³¹, repetidos aleatoriamente em 20 000 posições).

| método | tempo (ms) |
|---|---:|
| híbrida (**o melhor**) | 3,4 |
| rápida | 3,4 |
| base (**o que `ordenar` escolheu**) | 5,9 |
| `ordenar` (inclui 0,49 ms do `escolher`) | 6,5 |
| intercalação | 24,1 |

`ordenar` ficou **1,95× atrás** da melhor opção. *Por quê:* o `escolher` só enxerga
a faixa (`máx − mín ≈ 4,3·10⁹`), e ela é grande, então a contagem está
descartada e a base é a escolha "geral" para chaves grandes. Mas o dado tem só 5 valores
distintos, e a partição em 3 vias da rápida/híbrida tem custo O(n log d), com d
= nº de valores distintos, ou seja, quase linear. *Por que o `escolher` não vê:* contar
valores distintos exige um `set(v)`, que é O(n) com hash e não é barato; a amostra
de 256 elementos poderia revelar o padrão, mas não foi implementada, como melhoria
futura.

**Falha secundária — amostra de ordem enganada.** Se há poucas trocas (0,1%–0,5%),
os pares adjacentes amostrados podem ser todos crescentes, o `escolher` vê "0
descidas" e escolhe intercalação em vez de base. Perda medida: de 2× a 4× (intercalação
14–27 ms contra base 6–8 ms). É esse o erro que ocorreu em C com a amostra de 64.
Estimativa (modelo de Poisson sobre a densidade de descidas, não medida em muitas sementes): com 256 pares a chance de errar com 1% de trocas é <1%, e com 0,3% ainda ronda 20%.

## 6. Limites deste relatório

- Uma máquina, um núcleo, um tamanho principal (n=20 000). A calibração varre
  outros n (100 a 100 000), mas o benchmark "oficial" dos cenários não.
- `contagem` aparece como "recusa" nos cenários A e C porque a trava de segurança
  (`LIMITE_FAIXA_CONTAGEM = 10 milhões`) a impede de alocar dezenas de GB. Isso é
  comportamento projetado, não uma lentidão medida.
- "Híbrida" foi definida aqui como rápida com partição em 3 vias que passa a inserção em
  partições ≤ 32. Se no semestre a híbrida de vocês for outra (por exemplo
  intercalação + inserção), troquem a implementação e recalibrem.
- Os testes verificam correção, não desempenho (`tests/test_ordenacao.py`).
