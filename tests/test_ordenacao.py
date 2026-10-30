"""Testes: casos de borda exigidos + comparação com sorted() em dados aleatórios.

Rodar:  python -m unittest discover -s tests -v
"""
import random
import unittest

from ordenacao import METODOS, escolher, ordenar, contagem, FaixaGrandeDemais
from ordenacao import metodos

TODOS = dict(METODOS, ordenar=ordenar)

CASOS = {
    "vazia": [],
    "um_elemento": [7],
    "todos_iguais": [5] * 50,
    "ja_ordenada": list(range(100)),
    "invertida": list(range(100, 0, -1)),
    "negativos": [-3, 5, -10, 0, 7, -1, -10, 2],
    "so_negativos": [-5, -1, -9, -3, -3],
    "negativos_e_grandes": [-2**40, 2**40, 0, -1, 1, -2**40],
    "dois_elementos": [2, 1],
}


class TestCasosDeBorda(unittest.TestCase):
    def test_borda(self):
        for nome_caso, v in CASOS.items():
            esperado = sorted(v)
            for nome, f in TODOS.items():
                with self.subTest(caso=nome_caso, metodo=nome):
                    copia = list(v)
                    if (nome == "contagem" and v
                            and max(v) - min(v) > metodos.LIMITE_FAIXA_CONTAGEM):
                        # recusa por projeto: faixa grande demais
                        with self.assertRaises(FaixaGrandeDemais):
                            f(v)
                    else:
                        self.assertEqual(f(v), esperado)
                    self.assertEqual(v, copia, "a entrada não pode mudar")

    def test_casos_de_borda_grandes_o_bastante_para_cada_regra(self):
        """Os mesmos casos, mas com n suficiente para o `escolher` sair da
        inserção e exercitar contagem/intercalação/base/híbrida."""
        n = 2000
        casos = {
            "todos_iguais": [9] * n,
            "ja_ordenada": list(range(n)),
            "ja_ordenada_chaves_grandes": list(range(0, n * 10**6, 10**6)),
            "invertida": list(range(n, 0, -1)),
            "invertida_chaves_grandes": list(range(n * 10**6, 0, -10**6)),
            "negativos_faixa_estreita": [random.Random(1).randint(-50, 50) for _ in range(n)],
            "negativos_chaves_grandes": [random.Random(i).randint(-2**31, 0) for i in range(n)],
        }
        for nome_caso, v in casos.items():
            esperado = sorted(v)
            for nome, f in TODOS.items():
                with self.subTest(caso=nome_caso, metodo=nome):
                    if nome == "contagem" and max(v) - min(v) > metodos.LIMITE_FAIXA_CONTAGEM:
                        with self.assertRaises(FaixaGrandeDemais):
                            f(v)
                    else:
                        self.assertEqual(f(v), esperado)


class TestAleatorio(unittest.TestCase):
    def test_contra_sorted(self):
        rng = random.Random(42)
        for _ in range(200):
            n = rng.choice([0, 1, 2, 3, 10, 33, 100, 600])
            lo = rng.choice([-1000, -5, 0])
            hi = lo + rng.choice([0, 3, 100, 10**6, 2**40])
            v = [rng.randint(lo, hi) for _ in range(n)]
            esperado = sorted(v)
            for nome, f in TODOS.items():
                if nome == "contagem" and hi - lo > 10**6:
                    continue
                with self.subTest(n=n, faixa=(lo, hi), metodo=nome):
                    self.assertEqual(f(v), esperado)


class TestEscolher(unittest.TestCase):
    def test_minuscula_usa_insercao(self):
        self.assertEqual(escolher([3, 1, 2]), "insercao")

    def test_faixa_estreita_usa_contagem(self):
        v = [random.Random(0).randint(-500, 500) for _ in range(5000)]
        self.assertEqual(escolher(v), "contagem")

    def test_faixa_enorme_nunca_usa_contagem(self):
        """O aviso do enunciado: contagem com faixa grande estoura a memória."""
        rng = random.Random(0)
        v = [rng.randint(-2**40, 2**40) for _ in range(5000)]
        self.assertNotEqual(escolher(v), "contagem")
        # e dois pontos extremos bastam para tornar a faixa proibitiva
        w = [0, 10**12] + [rng.randint(0, 10) for _ in range(5000)]
        self.assertNotEqual(escolher(w), "contagem")
        self.assertEqual(ordenar(w), sorted(w))

    def test_ordenada_chaves_grandes_usa_intercalacao(self):
        v = list(range(0, 5000 * 10**6, 10**6))
        self.assertEqual(escolher(v), "intercalacao")

    def test_aleatoria_chaves_grandes_usa_base(self):
        rng = random.Random(0)
        v = [rng.randint(-2**31, 2**31) for _ in range(5000)]
        self.assertEqual(escolher(v), "base")

    def test_nao_inteiros_caem_no_caminho_generico(self):
        v = [3.5, 1.25, 2.0] * 100
        self.assertEqual(ordenar(v), sorted(v))

    def test_float_escondido_fora_da_amostra(self):
        v = list(range(1000, 0, -1))
        v[3] = 3.5                      # fora das posições amostradas
        self.assertEqual(ordenar(v), sorted(v))


if __name__ == "__main__":
    unittest.main()
