# Etapa 6 - Gerenciamento de Vendas

## Visao geral

Esta etapa implementou o modulo inicial de vendas do JOVE Manager.

O modulo permite registrar, editar, consultar, listar, filtrar, cancelar vendas
e registrar pagamentos posteriores. Os calculos financeiros usam `Decimal`.

## Funcionalidades entregues

- Listagem em `/sales`.
- Registro em `/sales/new`.
- Consulta em `/sales/{id}`.
- Edicao em `/sales/{id}/edit`.
- Cancelamento via `POST /sales/{id}/cancel`.
- Registro de pagamento via `POST /sales/{id}/payments`.
- API autenticada em `/api/sales` e `/api/sales/{id}`.
- Filtros por data, produto, cliente e status de pagamento.

## Regras implementadas

- Uma venda pode conter varios produtos no backend.
- Valor total e calculado automaticamente.
- Descontos sao considerados.
- Custo unitario, preco unitario e nome do produto sao gravados no item da
  venda para preservar o historico.
- Atualizar um produto nao altera vendas antigas.
- Valor vendido e valor recebido sao separados.
- Vendas canceladas recebem status de pagamento cancelado.
- Pagamentos posteriores atualizam status pendente, parcial ou pago.

## Observacao de interface

A estrutura de backend ja aceita varios itens por venda. Nesta primeira tela, o
formulario web trabalha com um item para manter a interface simples; a evolucao
para multiplos itens visuais pode ser feita sem alterar a regra central.

## Banco de dados

Migration criada:

```text
migrations/versions/20260922_004_sales_module.py
```

Ela adiciona campos financeiros/historicos em vendas e itens de venda, alem da
tabela `sale_payments`.

Comando executado:

```bash
alembic upgrade head
```

Resultado:

```text
20260922_004 (head)
```

## Testes

Arquivo criado:

```text
tests/test_sales.py
```

Os testes verificam:

- calculo de subtotal, desconto, total, custo e lucro bruto;
- preservacao do preco historico apos alteracao do produto;
- pagamento parcial e total;
- cancelamento;
- criacao via formulario autenticado;
- protecao da API de vendas.

Comando executado:

```bash
pytest -p no:cacheprovider
```

Resultado:

```text
35 passed
```

## Arquivos criados

- `app/schemas/sale.py`
- `app/repositories/sales.py`
- `app/services/sales.py`
- `app/routers/sales.py`
- `app/templates/sales/list.html`
- `app/templates/sales/form.html`
- `app/templates/sales/detail.html`
- `migrations/versions/20260922_004_sales_module.py`
- `tests/test_sales.py`
- `docs/etapa-6-vendas.md`

## Arquivos modificados

- `app/main.py`
- `app/models/enums.py`
- `app/models/sale.py`
- `app/models/__init__.py`
- `app/templates/base.html`
- `tests/test_models.py`
- `docs/README.md`

