# Etapa 10 - Dashboard Financeiro

## Objetivo

Esta etapa substitui o dashboard demonstrativo por uma visao financeira real,
alimentada diretamente pelo banco de dados do JOVE Manager.

O foco foi consolidar os principais indicadores da JOVE CREATE sem misturar
conceitos financeiros diferentes.

## Funcionalidades Entregues

- Faturamento por periodo.
- Valores recebidos por periodo.
- Valores pendentes.
- Custos dos produtos vendidos.
- Despesas operacionais.
- Lucro bruto.
- Lucro operacional estimado.
- Compras de filamentos.
- Investimentos em equipamentos.
- Quantidade de vendas.
- Ticket medio.
- Graficos em CSS para:
  - faturamento por mes;
  - despesas por categoria;
  - evolucao do lucro;
  - vendas por canal;
  - compras de materiais.
- Filtros:
  - hoje;
  - ultimos 7 dias;
  - mes atual;
  - mes anterior;
  - ano atual;
  - periodo personalizado.

## Regras Financeiras Aplicadas

- Faturamento considera vendas nao canceladas pela data da venda.
- Recebimentos consideram pagamentos pela data de pagamento.
- Valores pendentes sao calculados a partir de vendas nao canceladas ainda nao recebidas integralmente.
- Custo dos produtos vendidos usa o custo registrado no momento da venda.
- Lucro bruto = faturamento - custo dos produtos vendidos.
- Lucro operacional estimado = lucro bruto - despesas operacionais registradas.
- Compras de filamentos aparecem como compra de estoque, nao como custo integral dos produtos vendidos.
- Investimentos em equipamentos ficam separados das despesas operacionais.
- Despesas canceladas e vendas canceladas nao entram nos totais validos.

## Arquivos Criados

- `app/services/dashboard.py`
- `tests/test_dashboard.py`
- `docs/etapa-10-dashboard-financeiro.md`

## Arquivos Modificados

- `app/routers/home.py`
- `app/templates/index.html`
- `app/static/css/main.css`
- `docs/README.md`
- `README.md`

## Banco de Dados

Nao houve nova migration nesta etapa.

O dashboard utiliza as tabelas ja existentes:

- `sales`
- `sale_payments`
- `expenses`
- `financial_categories`
- `filament_purchases`
- `equipments`

## Interface

A tela principal em `/` agora exibe o dashboard financeiro real.

Em celulares, os indicadores e graficos ficam empilhados em cards verticais.
Em telas maiores, os indicadores e graficos usam grades para melhor leitura.

## Como Executar

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

Acesse:

```text
http://127.0.0.1:8000
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
56 passed
20260922_007 (head)
```

## Problemas Encontrados

Nao foi necessario alterar o banco de dados. O principal ajuste foi remover os
dados demonstrativos da pagina inicial e centralizar os calculos em
`app/services/dashboard.py`, para manter as regras financeiras fora da rota HTTP.
