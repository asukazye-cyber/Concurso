# Estratégia B — Dual Momentum com Filtro CDI (2027–2030)

**Mandato:** 48 meses, R$ 3.000 iniciais + R$ 200/mês, reinvestimento integral dos lucros líquidos, decisão ex-ante sem *look-ahead*.
**Status do documento:** especificação operacional + simulação de capitalização. **Não é previsão nem promessa de retorno.**

Arquivos que acompanham este documento:

| Arquivo | Conteúdo |
|---|---|
| `estrategia_b_2027_2030.py` | Cálculo dos cenários, ranking, filtro CDI, histerese, aporte e reserva de IR |
| `simulacao_2027_2030.csv` | 192 linhas: 4 cenários × 48 meses, com aportes, rendimentos e saldos |

---

## 0. Alertas antes dos números

1. **O horizonte é futuro.** Nenhuma simulação de 2027–2030 é backtest. A tabela da seção 2 é aritmética financeira (capitalização de uma taxa hipotética constante), não estimativa estatística. Momentum 6m é uma regra de alocação; a taxa final é consequência do mercado, não da regra.
2. **O hurdle CDI da premissa pode estar baixo.** Em 19/11/2026 a Selic meta é 13,75% a.a. e o CDI ~13,65% a.a. [1](https://www.meusdividendos.com/indicadores/selic) [5](https://www.idinheiro.com.br/investimentos/cdi/). O Focus de 16/11/2026 projeta Selic de 12,75% em 2027, 11,00% em 2028 e 10,50% em 2029 [1](https://bmcnews.com.br/economia/mercado-eleva-projecoes-de-inflacao-e-selic-para-2027-no-boletim-focus/). Portanto, **10,5% a.a. é plausível como CDI de fim de período, mas provavelmente subestima o CDI médio de 2027–2028**. O cenário "Conservador 12%" mal supera o custo de oportunidade realista se o CDI médio ficar em ~11%.
3. **20% e 28% a.a. nominais são agressivos.** Com IPCA projetado em 4%–5% [1](https://bmcnews.com.br/economia/mercado-eleva-projecoes-de-inflacao-e-selic-para-2027-no-boletim-focus/), 20% nominal ≈ 14%–15% real; 28% nominal ≈ 22%–23% real, todos os anos, por quatro anos. Trate-os como *stress positivo*, não como *base estatística*.
4. **O aporte de R$ 200 não compra uma cota de IVVB11.** A cota estava em ~R$ 478–485 em 2026 [5](https://statusinvest.com.br/etfs/ivvb11). Sem frações, parte do aporte precisa ficar em CDI até fechar uma cota inteira — isso está tratado na seção 3.

---

## 1. Especificação técnica da Estratégia B

### 1.1 Universo e veículo: B3 vs. exterior direto

| Bucket (fator) | Veículo B3 recomendado | Exposição BRL | Taxa de adm. referencial | Observação |
|---|---|---|---|---|
| Ações BR large | `BOVA11` | Ibovespa | ~0,10% a.a. | Maior liquidez da B3 [2](https://renovainvest.com.br/blog/lista-de-etf-conheca-todos-os-etfs-listados-na-b3/) |
| Ações BR small | `SMAL11` | SMLL | ~0,30% a.a. | Segundo ETF mais negociado no 1º sem./2026 [1](https://borainvestir.b3.com.br/tipos-de-investimentos/renda-variavel/etfs/os-etfs-que-dispararam-no-1o-semestre-chips-semicondutores-e-protecao-cambial-lideram-confira/) |
| Ações EUA/BRL | `IVVB11` | S&P 500 + USD/BRL embutidos | 0,23%–0,24% a.a. [4](https://br.investing.com/academy/etfs/ivvb11/) | Cota cara (~R$ 480) para aporte de R$ 200 |
| Ações EUA tech/BRL | `NASD11` | Nasdaq 100 + USD/BRL | ~0,30% a.a. [4](https://www.patrimo.app/blog/etfs-brasil-guia-completo-bova11-ivvb11/) | Cota menor (~R$ 22) [3](https://investidor10.com.br/etfs/) |
| Ouro | `GOLD11` | Ouro em BRL | conferir regulamento na data D | Cota baixa (~R$ 23) [3](https://investidor10.com.br/etfs/) |
| Cripto (opcional) | `HASH11` | Índice de cripto em BRL | conferir regulamento na data D | −40,49% no 1º sem./2026: risco extremo [1](https://borainvestir.b3.com.br/tipos-de-investimentos/renda-variavel/etfs/os-etfs-que-dispararam-no-1o-semestre-chips-semicondutores-e-protecao-cambial-lideram-confira/) |
| Defensivo | LCI/LCA/CDB ~100% DI | CDI | 0 (vehicle) | LCI/LCA isentos de IR; CDB tributado na tabela regressiva |

**Decisão: executar via ETFs líquidos da B3.** Com R$ 3.000 + R$ 200/mês, a exposição direta no exterior é economicamente inferior:

| Item | ETF B3 | Exposição direta no exterior |
|---|---|---|
| IOF | zero na compra/venda de cota | 1,10% na remessa para investimento + 0,38% no retorno [2](https://leonardomarks.com/iof-no-cambio-para-brasileiros-no-exterior-2026-aliquotas-regras-e-como-pagar-menos-imposto/) [3](https://carvalhobarros.adv.br/blog/artigos/trazer-dinheiro-do-exterior-para-o-brasil-imposto) |
| Spread cambial | embutido no ETF, indireto | ~0,3%–0,8% por conversão, duas vezes por giro |
| IR | 15% sobre ganho realizado, DARF mensal 6015, **sem isenção de R$ 20 mil** [1](https://renovainvest.com.br/blog/lista-de-etf-conheca-todos-os-etfs-listados-na-b3/) [3](https://www.patrimo.app/blog/day-trade-vs-swing-trade-ir-2026-aliquotas-darf) | 15% fixo sobre rendimentos, apuração anual na DAA (Lei 14.754/2023) [5](https://www.infomoney.com.br/guias/tributacao-sobre-investimentos-no-exterior/) |
| Custo fixo | corretagem zero; escolher corretora sem custódia | taxa mensal/conta + CBE quando aplicável |
| Adequação a R$ 200/mês | alta (cotas de R$ 22 a R$ 166 permitem acumular) | baixa: IOF de R$ 2,20 por aporte = R$ 26,40/ano, ~3% do lucro do 1º ano no cenário base, antes do spread cambial |

**Regra de elegibilidade do universo (anti-*look-ahead* e anti-sobrevivência):** na data de decisão D, o ativo precisa ter (i) pelo menos 6 meses de histórico de cota ajustada, (ii) volume médio diário ≥ R$ 1 milhão nos 20 pregões anteriores e (iii) regulamento com taxa conhecida. Ativos listados depois do início da janela **nunca** entram no histórico. A lista acima é o universo candidato de 2026; a lista elegível de cada mês é recalculada somente com dados de D.

### 1.2 Regra exata de decisão (todos os meses)

Seja **D** o último dia útil do mês e **D−6** o último dia útil seis meses antes.

1. **Coleta com data congelada.** Preços *ajustados* de D e D−6 (proventos já reinvestidos na cota), tal como divulgados em D. Guarde *snapshots* com a data de consulta: usar cota ajustada republicada depois de D (por exemplo, após um evento societário) injeta informação futura.
2. **Momentum em BRL.** `m_i = P_ajustado_i(D) / P_ajustado_i(D−6) − 1`. Para ETFs B3 isso **já inclui câmbio** (IVVB11 e NASD11 são cotados em reais e lastreados em dólar [3](https://investirecocaresocomecar.com.br/o-que-e-ivvb11/)). Se algum ativo for mantido diretamente no exterior: `m_BRL = (1 + m_local) * (USD/BRL_D / USD/BRL_D−6) − 1`, usando PTAX de fechamento de D e D−6.
3. **Filtro CDI.** `cdi_6m = Π(1 + DI_d/100) − 1` sobre os dias úteis de D−6 a D−1, com a taxa diária DI da série SGS 12 do BACEN [1](https://www.traderbrasil.com/blog/o-que-e-cdi.php) [4](https://neuriz.com/solucoes/series-bacen-revisional.html). **Usar D−1 e não D:** a taxa DI de D é apurada/divulgada após o fechamento, tipicamente no dia útil seguinte; incluí-la em uma decisão tomada em D seria *look-ahead*. Alternativa equivalente: decidir em D+1 antes da abertura, com DI já publicada até D, e executar no pregão de D+1.
4. **Elegibilidade.** Ativo de risco entra apenas se `m_i > cdi_6m` (estritamente). Se **nenhum** passa → 100% CDI. Se **um** passa → 50% ativo + 50% CDI. Se **dois ou mais** passam → Top 2 por `m_i`, 50%/50%.
5. **Um ativo por bucket.** IVVB11 e NASD11 pertencem ao mesmo bucket "EUA/BRL"; BOVA11 e SMAL11 ao bucket "ações BR". Escolhe-se o melhor de cada bucket antes de ranquear. Isso evita que o "Top 2" seja 100% renda variável americana com dois tickers correlacionados.
6. **Banda de tolerância (histerese).** O ativo já em carteira recebe **+1,0 p.p.** no ranking; a troca só ocorre se o desafiante vencer por **mais de 1,0 p.p. no ranking ajustado**, o que equivale a exigir **>2,0 p.p. de diferença bruta** em 6 meses. Limite de giro: no máximo **uma substituição por mês**.
7. **Banda de peso.** Alvo 50/50; aceitar deriva entre 45% e 55% sem negociar. Só rebalancear se o peso sair dessa faixa **ou** se houver troca de ativo.
8. **Aporte de R$ 200.** Vai integralmente para o líder elegível enquanto o peso dele for ≤55%; se ele já estiver em 55%, o aporte vai para o outro ativo (ou para o CDI no modo defensivo). Isso reduz venda forçada e custos. Se o aporte não comprar uma cota inteira, fica em CDI até completar o valor da cota na próxima decisão — sem perseguir preço intra-mês.
9. **Execução.** Ordens no pregão de D+1, sem operações de day trade (evita 20% de IR). Compras e vendas na mesma sessão para o ativo trocado.

### 1.3 Reinvestimento, custos e tributação

Para cada venda no mês:

```
resultado_i    = quantidade_i × (preço_venda_i − preço_médio_i)
base_ir        = max(0, Σ ganhos − Σ perdas)      # compensação no mês, mesma modalidade
reserva_ir     = 0,15 × base_ir                    # ETF B3 swing trade
caixa_líquido  = valor_das_vendas − spread − reserva_ir
```

- O **saldo líquido** volta para a carteira no mesmo fechamento: é ele que gera juros compostos. A `reserva_ir` fica em CDI até o vencimento da DARF 6015 (último dia útil do mês seguinte) [2](https://blueconsult.com.br/etf-de-bitcoin-b3-tributacao/).
- **IR de 15% incide sobre todo ganho de ETF**, sem a isenção de R$ 20 mil/mês das ações individuais [1](https://renovainvest.com.br/blog/lista-de-etf-conheca-todos-os-etfs-listados-na-b3/). Em operação comum não há day trade; a alíquota de 20% é evitada por construção.
- **Custos modelados:** taxa de administração do ETF embutida na cota (0,10%–0,30% a.a.); spread de 0,10% por lado em BOVA11/IVVB11 e 0,30% em ETFs de menor liquidez; corretagem zero e custódia zero (usar corretora sem tarifa — ver seção 3); IR conforme acima.
- **CDI:** se o veículo for LCI/LCA, o 10,5% é líquido; se for CDB 100% DI, a taxa líquida cai para `10,5% × (1 − 0,15) = 8,93%` na tabela regressiva.

---

## 2. Simulação 2027–2030 (48 meses)

**Metodologia (auditável):**

```
r_mensal           = (1 + R_anual)^(1/12) − 1            # geométrico, nunca R/12
saldo_com          = (saldo_anterior + 200) × (1 + r_mensal)
saldo_sem          = 12.600 + Σ[t=0..47] r_mensal × (3.000 + 200×(t+1))
ganho_extra        = saldo_com − saldo_sem
```

- Aportes em **t = 0, 1, …, 47** (início de cada mês); principal próprio total = R$ 12.600.
- "**Com reinvestimento**": lucro permanece na carteira e capitaliza sobre o total.
- "**Sem reinvestimento**": lucro de cada mês é retirado para caixa remunerado a **0%**; o principal continua investido. É um contrafactual deliberadamente conservador: se o caixa render CDI, o patrimônio final sem reinvestir sobe e o *ganho extra* cai.
- As taxas abaixo são **líquidas de custos e IR estimados**. A ponte bruto → líquido está logo após a tabela.

| Cenário | Taxa anual efetiva (líquida) | Total aportado | Patrimônio final **com** reinvestimento | Patrimônio final **sem** reinvestimento | Ganho extra (juros compostos) | Lucro total sobre principal |
|---|---:|---:|---:|---:|---:|---:|
| Conservador | 12,0% | R$ 12.600,00 | **R$ 16.923,61** | R$ 16.198,15 | R$ 725,46 | R$ 4.323,61 |
| Base Realista | 20,0% | R$ 12.600,00 | **R$ 20.460,83** | R$ 18.405,35 | R$ 2.055,47 | R$ 7.860,83 |
| Otimista | 28,0% | R$ 12.600,00 | **R$ 24.597,55** | R$ 20.481,57 | R$ 4.115,98 | R$ 11.997,55 |
| Benchmark 100% CDI | 10,5% | R$ 12.600,00 | **R$ 16.321,76** | R$ 15.768,28 | R$ 553,49 | R$ 3.721,76 |

**Leitura correta do "ganho extra":** ele mede apenas o efeito de *juros sobre juros*. No cenário Base, 26% do lucro total (R$ 2.055 / R$ 7.861) vem da capitalização; no Conservador, 17%. O ganho extra é pequeno nos primeiros anos e domina o resultado apenas com capital maior ou prazo maior — por isso o aporte recorrente importa mais que a taxa nos primeiros 24 meses.

**Instantâneos anuais do cenário Base (com reinvestimento):** 2027 R$ 6.252,76 · 2028 R$ 10.156,08 · 2029 R$ 14.840,05 · 2030 R$ 20.460,83.

### 2.1 Sensibilidade: e se 12/20/28% forem retornos **brutos**?

Arrasto anual estimado = 0,20% (taxa do ETF) + 0,20% (spread de 0,10% por lado com giro anual de 100% do patrimônio) + 15% × 50% do ganho bruto (metade dos ganhos realizada no ano).

| Cenário | Bruto | Arrasto estimado | Líquido | Patrimônio final líquido |
|---|---:|---:|---:|---:|
| Conservador | 12,0% | 1,30% | 10,70% | R$ 16.400,94 |
| Base | 20,0% | 1,90% | 18,10% | R$ 19.568,96 |
| Otimista | 28,0% | 2,50% | 25,50% | R$ 23.236,32 |

**Consequência prática:** se 12% for bruto, o resultado fica apenas R$ 79 acima do CDI 10,5% líquido — insuficiente para remunerar o risco de renda variável. Exija folga mínima de **3 p.p. sobre o CDI projetado** para aceitar o risco; com CDI médio de 11%, isso significa ~14% líquidos.

---

## 3. Auditoria de riscos e falhas potenciais (2027–2030)

| # | Falha provável | Mecanismo / evidência | Mitigação ex-ante | Gatilho de parada / monitor |
|---|---|---|---|---|
| 1 | **Whipsaw** em mercado lateral | Momentum 6m com janelas sobrepostas gira duas vezes seguidas e paga spread + 15% de IR em cada ida e volta | Banda de 2 p.p. brutos, bônus de 1 p.p. ao titular, máximo de 1 troca/mês, banda de peso 45–55% | >2 trocas por ano ou custos + IR >1,0% da carteira em 12m → dobrar a banda para 4 p.p. |
| 2 | **Reversão rápida do USD/BRL** | Em 2025, ganho em dólar (ex.: SMH) foi comprimido pela queda de ~R$ 6,21 para ~R$ 5,50; em 2026 o ETF com proteção cambial superou IVVB11 por ~11 p.p. no semestre [1](https://borainvestir.b3.com.br/tipos-de-investimentos/renda-variavel/etfs/os-etfs-que-dispararam-no-1o-semestre-chips-semicondutores-e-protecao-cambial-lideram-confira/) | IVVB11/NASD11 já rendem em reais; bucket "EUA/BRL" limitado a 50%; nunca comprar o mesmo fator duas vezes; sem hedge explícito (custo come o edge) | Se USD/BRL cair >10% em 6m e o momentum em BRL virar negativo, filtro CDI desliga o ativo automaticamente |
| 3 | **Tributação sobre giro** | ETF B3 paga 15% em **todo** ganho realizado; não há isenção de R$ 20 mil [1](https://renovainvest.com.br/blog/lista-de-etf-conheca-todos-os-etfs-listados-na-b3/) | Aportes ao líder em vez de vender; banda; sem day trade; reserva de 15% antes de reinvestir; DARF 6015 em dia | IR pago no ano >1,5% do patrimônio → reduzir a frequência de troca |
| 4 | **Custo fixo devora aporte de R$ 200** | R$ 10/mês de custódia = R$ 120/ano = 4% de R$ 3.000; IOF de 1,1% no exterior = R$ 2,20 por aporte | Corretora sem custódia e corretagem zero; uma ordem consolidada por mês; ETFs de cota baixa para sobras | Qualquer tarifa >R$ 0/mês ou >0,1% por operação → trocar de corretora/veículo |
| 5 | **Aporte não compra cota inteira** | 1 cota de IVVB11 ≈ R$ 480 > R$ 200 [5](https://statusinvest.com.br/etfs/ivvb11) | Manter sobra em CDI; `quantidade = floor(caixa_disponível / preço_da_cota)`; comprar só no fechamento de D+1; aceitar 45–55% de peso | Caixa parado >10% da carteira por >2 meses → migrar o bucket EUA para ticker de cota menor |
| 6 | **Look-ahead / sobrevivência** | Cota ajustada republicada após D, índice com componentes atuais, CDI de D divulgado em D+1 | Snapshot de dados com carimbo de data; universo reavaliado em D; CDI até D−1; exigir 6m de histórico e ADTV ≥ R$ 1 mi | Qualquer série sem carimbo de data → descartar o sinal daquele mês e ficar em CDI |
| 7 | **Mudança tributária 2027–2030** | Regras de offshore, IOF e IR podem mudar; IRPFM a partir do ano-calendário 2026 para rendas >R$ 600 mil [5](https://www.infomoney.com.br/guias/tributacao-sobre-investimentos-no-exterior/) | Revisar regulamento e alíquotas todo janeiro; simulação usa 15%; se a alíquota subir, recalcular a ponte bruto→líquido | Alíquota efetiva >18% → revisar para baixo a taxa base |
| 8 | **Risco de modelo / overfitting** | 6m é janela curta; 48 meses podem conter poucos episódios de tendência; HASH11 caiu 40% em 6 meses em 2026 | Universe fixo e simples, sem otimização de parâmetros; cripto é opcional e nunca obrigatório; respeitar o filtro CDI | Dois meses consecutivos no CDI é *feature*, não falha: o objetivo do filtro é preservar capital |
| 9 | **Risco de sequência e liquidez forçada** | Com R$ 12.600 de principal, uma retirada de emergência destrói o efeito composto | Reserva separada de 3–6 meses de despesas **fora** desta carteira; este capital é somente longo prazo | Qualquer necessidade de resgate → suspender aportes antes de vender com prejuízo |

**O que a lição de 2021–2025 ensina e o que não ensina:** a rotação para CDI foi o que preservou capital quando o momentum enfraqueceu; por isso o filtro absoluto é a parte mais importante da regra — mais até que a escolha do Top 2. Mas o mesmo filtro **não protege contra um tombo intra-mês**: ele só atua no fechamento seguinte.

---

## 4. Checklist operacional mensal

**No último dia útil do mês (D), após o fechamento:**

1. Baixar cota ajustada de cada ticker elegível em D e D−6, com carimbo da data de consulta.
2. Baixar DI diária (SGS 12) de D−6 a **D−1**; calcular `cdi_6m`.
3. Calcular `m_i` de cada ativo em BRL; descartar os que não têm 6 meses de histórico ou liquidez mínima.
4. Aplicar `m_i > cdi_6m`. Se nenhum passar → escrever "100% CDI" e pular para o passo 8.
5. Escolher o melhor de cada bucket; ordenar por momentum; aplicar o bônus de 1 p.p. ao titular e a banda de 2 p.p.
6. Conferir pesos atuais: se todos estiverem entre 45% e 55% e os tickers não mudaram → **não negociar**.
7. Se houver venda: calcular preço médio, `base_ir`, reserva de 15% e separar a DARF 6015.
8. Destinar os R$ 200: líder elegível (até 55%), outro ativo ou CDI; sobras para completar cotas inteiras ficam no CDI.
9. **No pregão de D+1:** executar as ordens consolidadas; reinvestir o líquido da venda já no mesmo dia.
10. Registrar em planilha: data da decisão, data da execução, sinais, pesos antes/depois, custos e IR estimado. Anualmente (janeiro): revisar universo, alíquotas e taxa de custódia.

### Código de execução do cálculo mensal

O módulo `estrategia_b_2027_2030.py` contém as funções Auditáveis. Para usar com dados reais:

```python
from estrategia_b_2027_2030 import (
    cdi_acumulado_6m, momentum_6m, escolher_top2,
    alocar_aporte, reserva_ir, Venda,
)

# Dados de D (preços ajustados congelados na data da consulta)
precos = {
    "BOVA11": (166.58, 155.10),   # (D, D-6) — substituir por dados reais
    "IVVB11": (478.09, 430.00),
    "NASD11": (21.74, 19.90),
    "GOLD11": (23.00, 21.50),
    "HASH11": (10.00, 12.00),
}
momentos = {t: momentum_6m(p_d, p_6) for t, (p_d, p_6) in precos.items()}

# SGS 12: taxas diárias (%) de D-6 a D-1 — NUNCA incluir D
di_diario = [0.0529] * 126
cdi6 = cdi_acumulado_6m(di_diario)

buckets = {
    "BOVA11": "acoes_br", "IVVB11": "acoes_eua", "NASD11": "acoes_eua",
    "GOLD11": "ouro", "HASH11": "cripto",
}
carteira_atual = {"BOVA11", "IVVB11"}
pesos = escolher_top2(momentos, buckets, cdi6, carteira_atual)
aporte = alocar_aporte(pesos, lider=max(pesos, key=pesos.get))

vendas = [Venda("IVVB11", 3, 478.09, 440.00)]  # exemplo: substituir pela venda real
ir = reserva_ir(vendas)

print("CDI 6m:", f"{cdi6:.2%}")
print("Momentum:", {k: f"{v:.2%}" for k, v in momentos.items()})
print("Alvo:", pesos)
print("Aporte R$200:", aporte)
print("Reserva IR:", ir["reserva_ir"])
```

> Os números do bloco acima são **ilustrativos**. Substitua pelos dados de D antes de operar. Para gerar a tabela e a série de 48 meses: `python3 estrategia_b_2027_2030.py`.

**Prompt pronto para o fechamento mensal (copiar e preencher):**

> "Usando exclusivamente cotações ajustadas e taxas DI disponíveis até o último dia útil de [MÊS/ANO], calcule o momentum de 6 meses em BRL de BOVA11, IVVB11, NASD11, GOLD11 e HASH11, o CDI acumulado de 6 meses (SGS 12, até D−1), aplique o filtro `m > CDI`, o bônus de 1 p.p. ao titular e a banda de 2 p.p., e devolva: (a) ativos elegíveis, (b) pesos alvo 50/50 ou 100% CDI, (c) destino do aporte de R$ 200 respeitando o teto de 55%, (d) quantidade inteira de cotas compráveis com a sobra, (e) reserva de IR de 15% sobre vendas com lucro. Não use nenhum dado posterior à data de corte."

---

## 5. Fontes consultadas

1. Selic 13,75% e CDI 13,65% (nov/2026): [meusdividendos](https://www.meusdividendos.com/indicadores/selic) e [idinheiro](https://www.idinheiro.com.br/investimentos/cdi/).
2. Séries SGS 432/12/4389 e metodologia do DI: [traderbrasil](https://www.traderbrasil.com/blog/o-que-e-cdi.php), [neuriz](https://neuriz.com/solucoes/series-bacen-revisional.html).
3. Focus nov/2026 (Selic 2027 12,75%; 2028 11%; 2029 10,5%; IPCA 2027 5%): [BM&C](https://bmcnews.com.br/economia/mercado-eleva-projecoes-de-inflacao-e-selic-para-2027-no-boletim-focus/).
4. ETFs B3, taxas e liquidez: [B3/Bora Investir](https://borainvestir.b3.com.br/tipos-de-investimentos/renda-variavel/etfs/os-etfs-que-dispararam-no-1o-semestre-chips-semicondutores-e-protecao-cambial-lideram-confira/), [Renova Invest](https://renovainvest.com.br/blog/lista-de-etf-conheca-todos-os-etfs-listados-na-b3/), [Investing.com](https://br.investing.com/academy/etfs/ivvb11/), [Patrimo](https://www.patrimo.app/blog/etfs-brasil-guia-completo-bova11-ivvb11).
5. Tributação: ETF B3 15% sem isenção de R$ 20 mil e DARF 6015 ([Renova](https://renovainvest.com.br/blog/lista-de-etf-conheca-todos-os-etfs-listados-na-b3/), [Patrimo](https://www.patrimo.app/blog/day-trade-vs-swing-trade-ir-2026-aliquotas-darf), [Blue Consult](https://blueconsult.com.br/etf-de-bitcoin-b3-tributacao/)); exterior 15% anual pela Lei 14.754/2023 ([InfoMoney](https://www.infomoney.com.br/guias/tributacao-sobre-investimentos-no-exterior/)); IOF 1,10% na remessa e 0,38% no retorno ([Leonardo Marks](https://leonardomarks.com/iof-no-cambio-para-brasileiros-no-exterior-2026-aliquotas-regras-e-como-pagar-menos-imposto/), [Carvalho Barros](https://carvalhobarros.adv.br/blog/artigos/trazer-dinheiro-do-exterior-para-o-brasil-imposto)).

*Este material é educacional e não constitui recomendação de investimento. Rentabilidade passada ou cenários hipotéticos não garantem resultados futuros.*
