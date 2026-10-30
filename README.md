# Auto Sort

Projeto desenvolvido para comparar seis algoritmos de ordenação e implementar um mecanismo de escolha automática do método mais adequado para cada entrada.

A função `escolher(v)` analisa características da lista e retorna o nome do algoritmo selecionado. A função `ordenar(v)` utiliza essa decisão e devolve uma nova lista ordenada, sem modificar a lista original.

## Objetivos

- Implementar seis métodos de ordenação estudados no semestre.
- Criar um seletor adaptativo que escolha um método conforme as características da entrada.
- Comparar o desempenho do seletor com cada algoritmo executado individualmente.
- Avaliar o custo de analisar a lista antes de ordená-la.
- Identificar situações em que o seletor pode tomar uma decisão que não é a mais rápida.

## Algoritmos implementados

| Método | Descrição |
|---|---|
| Inserção (`insercao`) | Ordenação por inserção. |
| Intercalação (`intercalacao`) | Merge Sort, baseado na divisão e intercalação de partes da lista. |
| Rápida (`rapida`) | Quick Sort com escolha aleatória do pivô. |
| Híbrida (`hibrida`) | Quick Sort com partição em três partes e uso de inserção em partições pequenas. |
| Contagem (`contagem`) | Counting Sort, indicado quando a faixa de valores é relativamente pequena. |
| Base (`base`) | Radix Sort, que organiza números por seus dígitos/bytes. |

Os métodos recebem uma lista de inteiros e retornam uma nova lista ordenada. A entrada original é preservada.

## Como o seletor funciona

A função `escolher(v)`, implementada em `ordenacao/escolhedor.py`, utiliza regras e limites calibrados por medições:

- **Listas pequenas:** escolhe inserção para entradas com até 32 elementos.
- **Valores inteiros em faixa estreita:** considera Counting Sort quando a faixa de valores é pequena em relação ao tamanho da lista.
- **Proteção de memória:** verifica o tamanho da faixa antes de selecionar Counting Sort, evitando alocações excessivas.
- **Entradas aparentemente ordenadas:** analisa uma amostra de pares adjacentes e pode selecionar Merge Sort.
- **Listas maiores com inteiros e quantidade adequada de passadas:** considera Radix Sort.
- **Outros casos:** utiliza o método híbrido como alternativa geral.

A análise da ordem é feita por amostragem, em vez de percorrer todos os elementos comparando-os em Python. Ainda assim, calcular mínimo e máximo exige percorrer a lista. O custo dessa análise é medido separadamente pelos benchmarks.

As regras e os valores utilizados estão documentados em `ordenacao/escolhedor.py` e detalhados no `RELATORIO.md`.

## Estrutura do projeto

```text
ordenacao-adaptativa/
├── ordenacao/
│   ├── __init__.py
│   ├── metodos.py
│   └── escolhedor.py
├── benchmarks/
│   ├── __init__.py
│   ├── _tempo.py
│   ├── medir.py
│   ├── calibrar.py
│   ├── custo_escolher.py
│   └── gerar_relatorios.py
├── tests/
│   ├── test_ordenacao.py
│   └── test_relatorio.py
├── relatorios/
│   ├── 01_testes_borda.csv
│   ├── 02_tabela_cenarios.csv
│   ├── 03_vencedores.csv
│   ├── 04_regras_escolher.csv
│   ├── 05_custo_escolher.csv
│   ├── 06_cenario_de_erro.csv
│   ├── 07_pior_caso_relativo.csv
│   └── relatorio.png
├── main.py
├── requirements.txt
├── README.md
└── RELATORIO.md
```

> Os arquivos de resultados são exemplos gerados em um ambiente específico. Os tempos podem variar conforme o computador, a versão do Python e a carga do sistema.

## Requisitos

- Python 3.10 ou superior.
- `matplotlib` para gerar gráficos.

Os algoritmos, testes e arquivos CSV não dependem de bibliotecas externas além da biblioteca padrão do Python.

## Instalação

Clone o repositório e entre na pasta do projeto:

```bash
git clone URL_DO_REPOSITORIO
cd auto-sort
```

Opcionalmente, crie e ative um ambiente virtual:

```bash
python -m venv .venv
```

No Linux/macOS:

```bash
source .venv/bin/activate
```

No Windows:

```powershell
.venv\Scripts\activate
```

Instale as dependências:

```bash
python -m pip install -r requirements.txt
```

## Como utilizar

Exemplo de utilização das funções:

```python
from ordenacao import escolher, ordenar

valores = [5, -3, 9, 0, 5]

metodo = escolher(valores)
print("Método escolhido:", metodo)

resultado = ordenar(valores)
print("Lista ordenada:", resultado)
print("Lista original:", valores)
```

A função `escolher()` retorna o nome do método selecionado. A função `ordenar()` executa o método e retorna a lista ordenada.

## Executar os testes

Na raiz do projeto, execute todos os testes:

```bash
python -m unittest discover -s tests -v
```

Para executar apenas os testes dos algoritmos:

```bash
python -m unittest tests.test_ordenacao -v
```

Para executar apenas os testes relacionados aos relatórios:

```bash
python -m unittest tests.test_relatorio -v
```

Os testes incluem casos como:

- Lista vazia.
- Lista com um elemento.
- Todos os elementos iguais.
- Lista já ordenada.
- Lista em ordem inversa.
- Valores negativos.
- Comparação do resultado dos algoritmos com `sorted()`.

## Reproduzir as medições

### Gerar os relatórios detalhados

Execute na raiz do projeto:

```bash
python -m benchmarks.gerar_relatorios
```

Essa execução gera os arquivos CSV e o gráfico dentro da pasta `relatorios/`.

Também é possível executar uma versão mais rápida:

```bash
python -m benchmarks.gerar_relatorios --rapido
```

Outras opções:

```bash
# Definir o tamanho das entradas, a semente e a pasta de saída
python -m benchmarks.gerar_relatorios --n 50000 --semente 7 --saida minha_pasta

# Gerar CSV compatível com configurações comuns do Excel em português
python -m benchmarks.gerar_relatorios --excel

# Gerar os CSVs sem criar o gráfico
python -m benchmarks.gerar_relatorios --sem-grafico
```

### Gerar medições específicas

```bash
# Comparação dos algoritmos nos cenários
python -m benchmarks.medir

# Calibração dos limites utilizados pelo seletor
python -m benchmarks.calibrar

# Custo de execução da função escolher()
python -m benchmarks.custo_escolher
```

### Executar o script principal

O arquivo `main.py`, localizado na raiz, também executa os testes e compara os seis métodos fixos com `ordenar(v)`. Ao final, gera `resultados_ordenacao.csv` e `grafico_ordenacao.jpg` na raiz do projeto.

```bash
python main.py
```

É possível alterar o tamanho das entradas, o número de repetições e a semente aleatória:

```bash
python main.py --n 5000 --repeticoes 7 --semente 2024
```

Consulte `python main.py --help` para ver as opções disponíveis.

## Cenários avaliados

As medições detalhadas do projeto consideram quatro tipos de entrada:

1. **Aleatório com chaves grandes:** números inteiros distribuídos em uma faixa ampla.
2. **Faixa estreita:** números inteiros concentrados entre -500 e 500.
3. **Quase ordenado:** lista inicialmente ordenada com aproximadamente 1% de trocas.
4. **Lista minúscula:** entrada com poucos elementos.

A comparação considera os seis algoritmos fixos e o método adaptativo `ordenar(v)`. O custo de `escolher(v)` também é medido isoladamente.

## Resultados e relatório

O arquivo [`RELATORIO.md`](RELATORIO.md) apresenta:

- A tabela comparativa dos quatro cenários e dos seis algoritmos.
- O vencedor de cada cenário e a justificativa.
- As regras utilizadas por `escolher(v)` e a origem dos limites.
- O custo de execução do seletor e a avaliação de quando ele compensa.
- Um cenário em que a decisão do seletor não é a melhor.

Os CSVs e o gráfico da pasta `relatorios/` complementam a análise.

## Observações sobre os resultados

- Os tempos dependem do hardware, da versão do Python e dos processos em execução.
- Para uma comparação justa, utilize a mesma máquina, os mesmos tamanhos de entrada e a mesma semente.
- O projeto utiliza mediana das repetições para reduzir a influência de variações pontuais.
- A ordenação por contagem pode consumir muita memória quando a faixa de valores é grande. Por isso, o seletor verifica a faixa antes de escolhê-la.
- O custo de analisar a entrada também faz parte do desempenho total de `ordenar(v)` e deve ser considerado ao interpretar os resultados.

## Autor

Eduardo Araujo dos Santos

