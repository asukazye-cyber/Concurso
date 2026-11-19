#!/usr/bin/env python3
"""Estrategia B - Dual Momentum com Filtro CDI (2027-2030).

Duas responsabilidades neste modulo:

1. Simulacao de capitalizacao (tabela de cenarios + serie 2027-2030).
2. Logica ex-ante de ranking, filtro CDI, banda de histerese, aporte e reserva de IR.

Convencoes (nao negociaveis, para evitar viagem no tempo e dupla contagem):

- Juros: taxa anual EFETIVA convertida em taxa mensal geometrica
  r = (1 + R)^(1/12) - 1. Nunca usar R/12.
- Aportes: R$ 200 no INICIO de cada mes (t = 0, 1, ..., 47); capital inicial
  no inicio de t = 0. Total de principal proprio = 3000 + 48*200 = 12600.
- "Sem reinvestimento": lucro apurado no mes e retirado para caixa a 0% de
  remuneracao. O principal continua investido e volta a render no mes seguinte.
- "Com reinvestimento": lucro fica na carteira e capitaliza sobre o total.
- Backtest/execucao: nenhuma funcao deste modulo consulta precos ou taxas
  futuras; `escolher_top2` recebe apenas o que o chamador passou como corte D.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

CAPITAL_INICIAL = 3_000.0
APORTE_MENSAL = 200.0
MESES = 48
IR_VENDAS = 0.15          # ETF B3 em operacao comum (swing trade)
BONUS_INCUMBENTE = 0.01    # +1,0 p.p. de histerese para quem ja esta na carteira
BANDA_TROCA = 0.01        # so troca se o desafiante ganhar por > 1,0 p.p. efetivo
                          # (2,0 p.p. de diferenca bruta, pois o titular tem +1 p.p.)
LIMIAR_PESO = 0.55        # aporte vai para o lider enquanto ele nao ultrapassar 55%


@dataclass(frozen=True)
class Cenario:
    nome: str
    taxa_anual: float
    total_aportado: float
    final_com_reinvestimento: float
    final_sem_reinvestimento: float

    @property
    def ganho_extra(self) -> float:
        return self.final_com_reinvestimento - self.final_sem_reinvestimento

    @property
    def lucro_total(self) -> float:
        return self.final_com_reinvestimento - self.total_aportado


def taxa_mensal(taxa_anual_efetiva: float) -> float:
    """Converte taxa anual efetiva em taxa mensal efetiva equivalente."""
    return (1.0 + taxa_anual_efetiva) ** (1.0 / 12.0) - 1.0


def valor_futuro_reinvestindo(
    capital: float, aporte: float, meses: int, taxa_anual_efetiva: float
) -> float:
    """Anuidade-vencida-antecipada: aportes em t = 0 .. meses-1."""
    r = taxa_mensal(taxa_anual_efetiva)
    fator = (1.0 + r) ** meses
    return capital * fator + aporte * (1.0 + r) * (fator - 1.0) / r


def valor_futuro_sem_reinvestir(
    capital: float, aporte: float, meses: int, taxa_anual_efetiva: float
) -> float:
    """Lucro de cada mes vai para caixa a 0%; principal continua rendendo."""
    r = taxa_mensal(taxa_anual_efetiva)
    base = capital + aporte * meses
    juros_nao_capitalizados = r * (
        meses * capital + aporte * meses * (meses + 1) / 2.0
    )
    return base + juros_nao_capitalizados


def simular_cenario(nome: str, taxa_anual: float) -> tuple[Cenario, list[dict]]:
    r = taxa_mensal(taxa_anual)
    saldo = CAPITAL_INICIAL
    principal = CAPITAL_INICIAL
    lucros_retirados = 0.0
    linhas: list[dict] = []

    for mes in range(1, MESES + 1):
        ano = 2027 + (mes - 1) // 12
        mes_num = (mes - 1) % 12 + 1
        saldo_inicial = saldo
        saldo += APORTE_MENSAL            # aporte no inicio do mes
        principal += APORTE_MENSAL
        rendimento = saldo * r
        saldo_final = saldo + rendimento

        # percurso "sem reinvestir": rendimento sai, so o principal segue investido
        juro_sem_capitalizar = principal * r
        lucros_retirados += juro_sem_capitalizar

        linhas.append(
            {
                "cenario": nome,
                "mes": mes,
                "competencia": f"{ano:04d}-{mes_num:02d}",
                "taxa_anual_efetiva": taxa_anual,
                "taxa_mensal_efetiva": r,
                "saldo_inicial": round(saldo_inicial, 2),
                "aporte": APORTE_MENSAL,
                "base_apos_aporte": round(saldo, 2),
                "rendimento_mes": round(rendimento, 2),
                "saldo_final_com_reinvestimento": round(saldo_final, 2),
                "principal_acumulado": round(principal, 2),
                "lucro_retirado_no_mes": round(juro_sem_capitalizar, 2),
                "saldo_final_sem_reinvestimento": round(
                    principal + lucros_retirados, 2
                ),
            }
        )
        saldo = saldo_final

    cenario = Cenario(
        nome=nome,
        taxa_anual=taxa_anual,
        total_aportado=principal,
        final_com_reinvestimento=saldo,
        final_sem_reinvestimento=principal + lucros_retirados,
    )
    return cenario, linhas


# ---------------------------------------------------------------------------
# Logica de decisao mensal (sem look-ahead)
# ---------------------------------------------------------------------------

def cdi_acumulado_6m(taxas_diarias_pct: Iterable[float]) -> float:
    """CDI de 6 meses pela serie SGS 12 (taxa diaria, %). Somente dias D-6..D-1."""
    acumulado = 1.0
    for taxa_diaria_pct in taxas_diarias_pct:
        acumulado *= 1.0 + taxa_diaria_pct / 100.0
    return acumulado - 1.0


def momentum_6m(preco_ajustado_d: float, preco_ajustado_d_menos_6: float) -> float:
    """Retorno total em BRL de D-6 até D (preco ajustado = proventos reinvestidos)."""
    return preco_ajustado_d / preco_ajustado_d_menos_6 - 1.0


def momentum_em_brl_exterior(
    retorno_local: float, usdbrl_d: float, usdbrl_d_menos_6: float
) -> float:
    """Alternativa de exposicao direta: ativo no exterior + cambio (PTAX de fechamento)."""
    return (1.0 + retorno_local) * (usdbrl_d / usdbrl_d_menos_6) - 1.0


def escolher_top2(
    momentos: Mapping[str, float],
    buckets: Mapping[str, str],
    cdi_6m: float,
    carteira_atual: Iterable[str] = (),
) -> dict[str, float]:
    """Filtro CDI + Top 2 por bucket, com histerese de 2 p.p. de retorno bruto.

    Regra 3 ( rigorosa ): so entram ativos com momentum_6m > cdi_6m.
    Se nenhum passa -> 100% CDI. Se passa um -> 50% ativo / 50% CDI.
    Regra 4: no maximo um ativo por bucket, para nao somar duas vezes o mesmo fator
    (ex.: IVVB11 e NASD11 sao ambos "EUA/BRL").
    """
    atuais = set(carteira_atual)
    elegiveis = {
        ticker: mom for ticker, mom in momentos.items() if mom > cdi_6m
    }
    if not elegiveis:
        return {"CDI": 1.0}

    melhor_por_bucket: dict[str, tuple[str, float]] = {}
    for ticker, mom in elegiveis.items():
        bucket = buckets.get(ticker, ticker)
        if bucket not in melhor_por_bucket or mom > melhor_por_bucket[bucket][1]:
            melhor_por_bucket[bucket] = (ticker, mom)

    ajustado = {
        ticker: mom + (BONUS_INCUMBENTE if ticker in atuais else 0.0)
        for ticker, mom in elegiveis.items()
    }
    ranking = sorted(melhor_por_bucket.values(), key=lambda par: ajustado[par[0]], reverse=True)

    selecionados = [ticker for ticker, _ in ranking[:2]]

    # Banda de tolerancia: titular so sai se o desafiante vencer por mais de 1 p.p.
    # no ranking ajustado (equivalente a > 2 p.p. no retorno bruto de 6 meses).
    for titular in list(atuais):
        if titular in selecionados or titular not in ajustado:
            continue
        buckets_selecionados = {buckets.get(t, t) for t in selecionados}
        if buckets.get(titular, titular) in buckets_selecionados:
            continue  # nunca deixar dois ativos do mesmo fator entrarem pela banda
        posicao_titular = ajustado[titular]
        pior_selecionado = min(ajustado[t] for t in selecionados)
        if posicao_titular >= pior_selecionado - BANDA_TROCA:
            selecionados[-1] = titular

    if len(selecionados) == 1:
        return {selecionados[0]: 0.5, "CDI": 0.5}
    return {selecionados[0]: 0.5, selecionados[1]: 0.5}


def alocar_aporte(pesos: Mapping[str, float], lider: str | None) -> dict[str, float]:
    """Aporte novo vai ao lider ate o limite de 55% da carteira; depois equaliza."""
    aporte = {ticker: 0.0 for ticker in pesos}
    if not pesos:
        return aporte
    if lider is None or lider not in aporte or pesos[lider] > LIMIAR_PESO:
        # sem lider elegivel ou lider ja pesado: destina ao menor peso (equalizacao)
        lider = min(pesos, key=pesos.get)
    aporte[lider] = APORTE_MENSAL
    return aporte


@dataclass(frozen=True)
class Venda:
    ticker: str
    quantidade: float
    preco_venda: float
    preco_medio: float


def reserva_ir(vendas: Iterable[Venda], aliquota: float = IR_VENDAS) -> dict[str, float]:
    """Apura ganhos/perdas do mes por ETF e reserva IR antes de reinvestir."""
    ganhos = 0.0
    perdas = 0.0
    detalhes: dict[str, float] = {}
    for venda in vendas:
        resultado = venda.quantidade * (venda.preco_venda - venda.preco_medio)
        detalhes[venda.ticker] = detalhes.get(venda.ticker, 0.0) + resultado
    for resultado in detalhes.values():
        if resultado > 0:
            ganhos += resultado
        else:
            perdas += abs(resultado)
    base = max(0.0, ganhos - perdas)  # compensacao de prejuizos no mesmo mes/modalidade
    imposto = base * aliquota
    return {
        "ganhos": round(ganhos, 2),
        "perdas": round(perdas, 2),
        "base_ir": round(base, 2),
        "reserva_ir": round(imposto, 2),
        "aliquota": aliquota,
    }


def custo_media_anual(taxa_bruta: float, giro_one_way: float = 1.0) -> float:
    """Ponte bruto -> liquido usada apenas no teste de sensibilidade.

    admin 0,20% a.a. (embutida na cota) + spread 0,10% por lado * giro + IR
    de 15% sobre 50% do ganho bruto realizado no ano.
    """
    adm = 0.002
    spread = 0.001 * 2.0 * giro_one_way
    ir = IR_VENDAS * 0.5 * taxa_bruta
    return adm + spread + ir


# ---------------------------------------------------------------------------
# Entrega
# ---------------------------------------------------------------------------

CENARIOS = (
    ("Conservador", 0.12),
    ("Base Realista", 0.20),
    ("Otimista", 0.28),
    ("Benchmark 100% CDI", 0.105),
)


def main() -> None:
    print("Estrategia B | 2027-2030 | 48 meses | R$ 3.000 + R$ 200/mes")
    print("Convencao: taxa anual efetiva liquida; aporte no inicio do mes;")
    print("sem reinvestir = lucro retirado para caixa a 0%.\n")
    header = (
        f"{'Cenario':<20}{'Anual':>8}{'Aportado':>12}{'Com reinv.':>14}"
        f"{'Sem reinv.':>14}{'Extra':>11}{'Lucro total':>13}"
    )
    print(header)
    print("-" * len(header))
    todas_linhas: list[dict] = []
    for nome, taxa in CENARIOS:
        cenario, linhas = simular_cenario(nome, taxa)
        todas_linhas.extend(linhas)
        print(
            f"{cenario.nome:<20}{cenario.taxa_anual:>7.1%}"
            f"{cenario.total_aportado:>12,.2f}"
            f"{cenario.final_com_reinvestimento:>14,.2f}"
            f"{cenario.final_sem_reinvestimento:>14,.2f}"
            f"{cenario.ganho_extra:>11,.2f}"
            f"{cenario.lucro_total:>13,.2f}"
        )

    caminho_csv = Path(__file__).with_name("simulacao_2027_2030.csv")
    with caminho_csv.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(todas_linhas[0].keys()))
        escritor.writeheader()
        escritor.writerows(todas_linhas)
    print(f"\nSerie mensal (4 cenarios x 48 meses): {caminho_csv.name}")

    print("\nPonte bruto -> liquido (sensibilidade; nao e a tabela principal):")
    for nome, taxa in CENARIOS[:3]:
        arrasto = custo_media_anual(taxa)
        liquido = taxa - arrasto
        _, linhas = simular_cenario(nome + " (liquido)", liquido)
        print(
            f"  {nome:<14} bruto {taxa:.1%} - arrasto {arrasto:.2%} "
            f"= liquido {liquido:.2%} -> final R$ {linhas[-1]['saldo_final_com_reinvestimento']:,.2f}"
        )

    # Exemplo de decisao mensal com dados ficticios (apenas demonstracao da funcao).
    momentos_demo = {
        "BOVA11": 0.145, "IVVB11": 0.181, "NASD11": 0.224,
        "GOLD11": 0.132, "HASH11": -0.105,
    }
    buckets_demo = {
        "BOVA11": "acoes_br", "IVVB11": "acoes_eua", "NASD11": "acoes_eua",
        "GOLD11": "ouro", "HASH11": "cripto",
    }
    pesos_demo = escolher_top2(momentos_demo, buckets_demo, cdi_6m=0.065)
    print(f"\nDry-run (dados ficticios): {pesos_demo}")
    print(f"Aporte: {alocar_aporte(pesos_demo, lider=max(pesos_demo, key=pesos_demo.get))}")


if __name__ == "__main__":
    main()
