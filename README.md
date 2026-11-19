# Concurso

## Estratégia B — Dual Momentum com Filtro CDI (2027–2030)

- [ESTRATEGIA_B_2027_2030.md](ESTRATEGIA_B_2027_2030.md) — especificação técnica, tabela de simulação, auditoria de riscos e checklist operacional.
- [estrategia_b_2027_2030.py](estrategia_b_2027_2030.py) — cálculo dos cenários, ranking, filtro CDI, histerese, aporte e reserva de IR.
- [simulacao_2027_2030.csv](simulacao_2027_2030.csv) — série mensal dos 4 cenários (48 meses cada).

### Reproduzir

```bash
python3 estrategia_b_2027_2030.py    # imprime a tabela e reescreve o CSV
python3 -m unittest -v test_estrategia_b.py
```

As taxas anuais da simulação são **efetivas e líquidas**; o aporte entra no início de cada mês e a conversão para a taxa mensal é geométrica, `(1+R)^(1/12)-1`.
