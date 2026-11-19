"""Testes de sanidade da matematica e das regras da Estrategia B."""

import unittest

from estrategia_b_2027_2030 import (
    APORTE_MENSAL,
    CAPITAL_INICIAL,
    MESES,
    Venda,
    alocar_aporte,
    escolher_top2,
    reserva_ir,
    simular_cenario,
    taxa_mensal,
    valor_futuro_reinvestindo,
    valor_futuro_sem_reinvestir,
)


class TestCapitalizacao(unittest.TestCase):
    def test_taxa_mensal_efetiva(self):
        self.assertAlmostEqual((1 + taxa_mensal(0.12)) ** 12 - 1, 0.12, places=12)

    def test_formula_fechada_igual_a_iteracao(self):
        for taxa in (0.105, 0.12, 0.20, 0.28):
            cenario, linhas = simular_cenario("teste", taxa)
            self.assertAlmostEqual(
                cenario.final_com_reinvestimento,
                linhas[-1]["saldo_final_com_reinvestimento"],
                places=2,
            )
            self.assertAlmostEqual(
                valor_futuro_reinvestindo(CAPITAL_INICIAL, APORTE_MENSAL, MESES, taxa),
                cenario.final_com_reinvestimento,
                places=8,
            )
            self.assertAlmostEqual(
                valor_futuro_sem_reinvestir(CAPITAL_INICIAL, APORTE_MENSAL, MESES, taxa),
                cenario.final_sem_reinvestimento,
                places=8,
            )

    def test_principal_e_aportes(self):
        cenario, _ = simular_cenario("teste", 0.20)
        self.assertEqual(cenario.total_aportado, 12_600.0)


class TestRegras(unittest.TestCase):
    BUCKETS = {
        "BOVA11": "acoes_br", "SMAL11": "acoes_br",
        "IVVB11": "acoes_eua", "NASD11": "acoes_eua",
        "GOLD11": "ouro",
    }

    def test_filtro_defensivo(self):
        momentos = {"BOVA11": 0.05, "IVVB11": 0.06, "GOLD11": 0.03}
        self.assertEqual(escolher_top2(momentos, self.BUCKETS, 0.07), {"CDI": 1.0})

    def test_um_elegivel(self):
        momentos = {"BOVA11": 0.09, "IVVB11": 0.06}
        pesos = escolher_top2(momentos, self.BUCKETS, 0.07)
        self.assertEqual(pesos, {"BOVA11": 0.5, "CDI": 0.5})

    def test_top2_respeita_bucket(self):
        momentos = {"BOVA11": 0.15, "SMAL11": 0.20, "IVVB11": 0.18, "GOLD11": 0.10}
        pesos = escolher_top2(momentos, self.BUCKETS, 0.07)
        self.assertIn("SMAL11", pesos)
        self.assertIn("IVVB11", pesos)
        self.assertEqual(sum(pesos.values()), 1.0)

    def test_banda_mantem_titular(self):
        # IVVB11 (titular, melhor do bucket EUA) tem 18%; o segundo colocado
        # bruto e SMAL11 com 19%. Com o bonus de 1 p.p. o titular empata e fica.
        momentos = {"BOVA11": 0.10, "SMAL11": 0.19, "IVVB11": 0.18, "GOLD11": 0.195}
        pesos = escolher_top2(momentos, self.BUCKETS, 0.05, carteira_atual={"IVVB11"})
        self.assertIn("IVVB11", pesos)

    def test_banda_troca_com_vantagem_grande(self):
        momentos = {"BOVA11": 0.10, "IVVB11": 0.18, "NASD11": 0.23}
        pesos = escolher_top2(momentos, self.BUCKETS, 0.05, carteira_atual={"IVVB11"})
        self.assertIn("NASD11", pesos)
        self.assertNotIn("IVVB11", pesos)

    def test_aporte_vai_ao_lider(self):
        aporte = alocar_aporte({"BOVA11": 0.5, "IVVB11": 0.5}, lider="IVVB11")
        self.assertEqual(aporte["IVVB11"], 200.0)
        self.assertEqual(aporte["BOVA11"], 0.0)

    def test_reserva_ir_com_compensacao(self):
        vendas = [
            Venda("BOVA11", 10, 110, 100),   # +100
            Venda("GOLD11", 10, 95, 100),    # -50
        ]
        apuracao = reserva_ir(vendas)
        self.assertEqual(apuracao["base_ir"], 50.0)
        self.assertEqual(apuracao["reserva_ir"], 7.5)


if __name__ == "__main__":
    unittest.main()
