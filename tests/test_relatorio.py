"""Testa o gerador de relatórios (benchmarks/gerar_relatorios.py).

Roda o gerador em modo --rapido numa pasta temporária e confere que:
  - os testes de borda exigidos (vazia, 1 elemento, iguais, ordenada, invertida,
    negativos) estão no CSV e passaram;
  - a tabela tem os 4 cenários x 6 métodos;
  - cada cenário tem vencedor e "por quê"; as regras e o custo do `escolher`
    estão registrados; há um cenário de erro;
  - o gráfico é gerado (se matplotlib estiver instalado).
Não confere TEMPOS (dependem da máquina); confere as DECISÕES do `escolher`,
que são determinísticas para a semente fixa.

Rodar:  python -m unittest tests.test_relatorio -v      (~20 s)
"""
import csv
import os
import tempfile
import unittest

from benchmarks import gerar_relatorios as gr
from ordenacao import escolhedor as esc

try:
    import matplotlib  # noqa: F401
    TEM_MATPLOTLIB = True
except ImportError:
    TEM_MATPLOTLIB = False

METODOS_COLUNAS = ["insercao_ms", "intercalacao_ms", "rapida_ms", "hibrida_ms",
                   "contagem_ms", "base_ms"]


def ler(pasta, nome, delimiter=","):
    with open(os.path.join(pasta, nome), encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=delimiter))


class TestGeradorDeRelatorios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.pasta = cls._tmp.name
        cls.codigo = gr.main(["--rapido", "--saida", cls.pasta])

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_codigo_de_saida_zero(self):
        self.assertEqual(self.codigo, 0)

    def test_arquivos_gerados(self):
        esperados = ["01_testes_borda.csv", "02_tabela_cenarios.csv", "03_vencedores.csv",
                     "04_regras_escolher.csv", "05_custo_escolher.csv",
                     "06_cenario_de_erro.csv", "07_pior_caso_relativo.csv"]
        if TEM_MATPLOTLIB:
            esperados.append("relatorio.png")
        for nome in esperados:
            caminho = os.path.join(self.pasta, nome)
            with self.subTest(arquivo=nome):
                self.assertTrue(os.path.exists(caminho))
                self.assertGreater(os.path.getsize(caminho), 100)

    def test_borda_cobre_os_casos_exigidos_e_passa(self):
        linhas = ler(self.pasta, "01_testes_borda.csv")
        casos = {l["caso"] for l in linhas}
        for exigido in ("lista_vazia", "um_elemento", "todos_iguais",
                        "ja_ordenada", "invertida", "valores_negativos"):
            self.assertIn(exigido, casos)
        metodos = {l["metodo"] for l in linhas}
        self.assertEqual(metodos, {"insercao", "intercalacao", "rapida", "hibrida",
                                   "contagem", "base", "ordenar"})
        falhas = [l for l in linhas if l["resultado"].startswith("FALHOU")]
        self.assertEqual(falhas, [], falhas[:3])

    def test_tabela_quatro_cenarios_seis_metodos(self):
        linhas = ler(self.pasta, "02_tabela_cenarios.csv")
        principais = [l for l in linhas if l["cenario"][0] in "ABCD"]
        self.assertEqual([l["cenario"][0] for l in principais], list("ABCD"))
        for l in principais:
            for col in METODOS_COLUNAS + ["ordenar_ms"]:
                self.assertIn(col, l)
                self.assertNotEqual(l[col], "")

    def test_decisoes_do_escolher(self):
        por_letra = {l["cenario"][0]: l for l in ler(self.pasta, "02_tabela_cenarios.csv")}
        self.assertEqual(por_letra["A"]["escolher_escolheu"], "base")
        self.assertEqual(por_letra["B"]["escolher_escolheu"], "contagem")
        self.assertEqual(por_letra["D"]["escolher_escolheu"], "insercao")
        # C depende da amostra de ordem; com a semente fixa é base, mas
        # intercalação também é uma decisão válida do projeto.
        self.assertIn(por_letra["C"]["escolher_escolheu"], ("base", "intercalacao"))
        # a contagem tem de se recusar quando a faixa é gigante (A e C)
        self.assertEqual(por_letra["A"]["contagem_ms"], "recusa")

    def test_vencedores_com_por_que(self):
        linhas = ler(self.pasta, "03_vencedores.csv")
        self.assertEqual(len(linhas), 4)
        for l in linhas:
            self.assertTrue(l["vencedor"])
            self.assertGreater(len(l["por_que"]), 20)

    def test_regras_batem_com_as_constantes_do_codigo(self):
        linhas = ler(self.pasta, "04_regras_escolher.csv")
        self.assertEqual(len(linhas), 6)
        texto = " ".join(l["limiar"] for l in linhas)
        self.assertIn(f"N_MINUSCULA={esc.N_MINUSCULA}", texto)
        self.assertIn(f"RAZAO_CONTAGEM={esc.RAZAO_CONTAGEM}", texto)
        self.assertIn(f"AMOSTRA={esc.AMOSTRA}", texto)
        for l in linhas:
            self.assertTrue(l["origem"])

    def test_custo_do_escolher(self):
        linhas = ler(self.pasta, "05_custo_escolher.csv")
        self.assertEqual({l["tipo_de_dados"] for l in linhas}, {"chaves_grandes", "faixa_estreita"})
        for l in linhas:
            self.assertGreater(float(l["escolher_ms"]), 0)
            self.assertGreater(float(l["custo_pct"]), 0)

    def test_cenario_de_erro_documentado(self):
        linhas = ler(self.pasta, "06_cenario_de_erro.csv")
        self.assertTrue(any(l["cenario"].startswith("E.") for l in linhas))
        for l in linhas:
            self.assertGreater(len(l["por_que"]), 20)
        # E: o escolher escolhe base, mas a melhor opção é de comparação (híbrida/rápida)
        e = next(l for l in linhas if l["cenario"].startswith("E."))
        self.assertEqual(e["escolheu"], "base")
        self.assertIn(e["melhor_fixo"], ("hibrida", "rapida"))

    def test_pior_caso_relativo(self):
        linhas = {l["metodo"]: l for l in ler(self.pasta, "07_pior_caso_relativo.csv")}
        self.assertEqual(len(linhas), 7)          # 6 métodos + ordenar
        self.assertEqual(linhas["contagem"]["recusou_em_algum_cenario"], "SIM")
        # nenhum método fixo é tão robusto quanto o ordenar
        menor_fixo = min(float(l["pior_caso_x"]) for m, l in linhas.items() if m != "ordenar")
        self.assertLess(float(linhas["ordenar"]["pior_caso_x"]), menor_fixo)


class TestOpcaoExcel(unittest.TestCase):
    def test_csv_com_ponto_e_virgula_e_virgula_decimal(self):
        with tempfile.TemporaryDirectory() as pasta:
            gr.main(["--rapido", "--excel", "--sem-grafico", "--saida", pasta])
            self.assertFalse(os.path.exists(os.path.join(pasta, "relatorio.png")))
            linhas = ler(pasta, "05_custo_escolher.csv", delimiter=";")
            self.assertIn(",", linhas[0]["escolher_ms"])      # decimal com vírgula
            with open(os.path.join(pasta, "05_custo_escolher.csv"), "rb") as f:
                self.assertTrue(f.read(3) == b"\xef\xbb\xbf")  # BOM para o Excel


if __name__ == "__main__":
    unittest.main()
