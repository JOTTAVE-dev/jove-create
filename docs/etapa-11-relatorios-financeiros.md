# Etapa 11 - Relatorios Financeiros

## Objetivo

Esta etapa implementa o modulo de relatorios financeiros do JOVE Manager,
permitindo consultar informacoes consolidadas e detalhadas da operacao da
JOVE CREATE.

Os relatorios usam o mesmo motor financeiro do dashboard para evitar formulas
duplicadas.

## Relatorios Entregues

- Relatorio de vendas.
- Relatorio de despesas.
- Relatorio de compras.
- Relatorio de investimentos.
- Relatorio de faturamento.
- Relatorio de lucro.
- Relatorio de fluxo de caixa.

## Funcionalidades

- Selecao de periodo:
  - hoje;
  - ultimos 7 dias;
  - mes atual;
  - mes anterior;
  - ano atual;
  - periodo personalizado.
- Filtro por categoria.
- Filtro por canal de venda.
- Visualizacao em cards de resumo.
- Visualizacao em grafico de barras CSS.
- Visualizacao em tabela.
- Exportacao em CSV.
- Estrutura documentada para futura exportacao em Excel e PDF.

## Regras Financeiras

As regras foram centralizadas em `app/services/financials.py`.

Esse servico e utilizado pelo dashboard e pelos relatorios para manter
consistencia nos calculos:

- faturamento;
- recebimentos;
- pendencias;
- custo dos produtos vendidos;
- despesas operacionais;
- lucro bruto;
- lucro operacional estimado;
- compras de filamentos;
- investimentos em equipamentos;
- ticket medio.

## Arquivos Criados

- `app/services/financials.py`
- `app/services/reports.py`
- `app/routers/reports.py`
- `app/templates/reports/list.html`
- `tests/test_reports.py`
- `docs/etapa-11-relatorios-financeiros.md`

## Arquivos Modificados

- `app/services/dashboard.py`
- `app/main.py`
- `app/templates/base.html`
- `app/static/css/main.css`
- `docs/README.md`
- `README.md`

## Banco de Dados

Nao houve nova migration nesta etapa.

O modulo utiliza dados ja existentes de:

- vendas;
- pagamentos de vendas;
- despesas;
- categorias financeiras;
- compras de filamentos;
- equipamentos.

## Rotas

Interface web:

```text
/reports
```

Exportacao CSV:

```text
/reports/export.csv
```

API preparada para futuras integracoes:

```text
/api/reports
```

## Como Executar

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

Acesse:

```text
http://127.0.0.1:8000/reports
```

## Como Testar

Comandos executados:

```bash
python -m compileall app tests migrations
pytest -p no:cacheprovider
alembic current
```

Resultado:

```text
61 passed
20260922_007 (head)
```

## Problemas Encontrados

Nao foram encontrados problemas pendentes. Durante a implementacao, os calculos
do dashboard foram extraidos para `app/services/financials.py` para garantir
consistencia entre dashboard e relatorios.
