# Etapa 9 - Despesas Operacionais

## Objetivo

Esta etapa implementa o modulo de despesas do JOVE Manager para registrar,
acompanhar e consultar os gastos operacionais da JOVE CREATE.

O modulo diferencia despesa registrada de despesa paga, permite marcar despesas
recorrentes sem gerar duplicacoes automaticas e prepara indicadores por
categoria e por periodo.

## Funcionalidades Entregues

- Cadastro de despesas operacionais.
- Edicao de despesas existentes.
- Consulta detalhada de uma despesa.
- Listagem responsiva de despesas.
- Filtros por periodo, categoria, status e forma de pagamento.
- Registro de pagamento posterior.
- Marcacao de despesas recorrentes com intervalo em meses.
- Indicadores de total registrado, total pago, pendencias e vencidas.
- Resumo por categoria e por mes.

## Regras Implementadas

- Valores monetarios usam `Decimal`.
- Despesas canceladas nao entram nos totais principais.
- Totais do modulo consideram apenas categorias do tipo `operating_expense`.
- Compras de filamentos e investimentos em equipamentos continuam separados e
  nao sao duplicados nos totais de despesas operacionais.
- Despesas recorrentes recebem uma chave de controle para evitar duplicacao
  automatica futura.
- Uma despesa pode estar como pendente, paga, atrasada ou cancelada.

## Arquivos Criados

- `app/schemas/expense.py`
- `app/repositories/expenses.py`
- `app/services/expenses.py`
- `app/routers/expenses.py`
- `app/templates/expenses/list.html`
- `app/templates/expenses/form.html`
- `app/templates/expenses/detail.html`
- `migrations/versions/20260922_007_expenses_module.py`
- `tests/test_expenses.py`
- `docs/etapa-9-despesas.md`

## Arquivos Modificados

- `app/main.py`
- `app/models/enums.py`
- `app/models/finance.py`
- `app/templates/base.html`
- `tests/test_models.py`
- `docs/README.md`
- `README.md`

## Banco de Dados

A migration `20260922_007_expenses_module.py` adiciona campos ao modelo de
despesas para apoiar o modulo operacional:

- `expense_date`
- `paid_at`
- `payment_method`
- `is_recurring`
- `recurrence_months`
- `recurring_key`

Tambem foram criados indices para consultas frequentes por data, categoria,
status, forma de pagamento e recorrencia.

## Interface

A interface esta disponivel em:

```text
/expenses
```

As telas seguem o padrao visual responsivo ja criado para o projeto, com
cards de indicadores, filtros, tabela/listagem e formularios adaptados para
celular.

## Como Executar

Instale as dependencias, aplique as migrations e suba o servidor:

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Depois acesse:

```text
http://127.0.0.1:8000/expenses
```

## Como Testar

Comando executado nesta etapa:

```bash
pytest -p no:cacheprovider
```

Resultado:

```text
53 passed
```

Tambem foi executado:

```bash
python -m compileall app tests migrations
alembic current
```

O Alembic ficou em:

```text
20260922_007 (head)
```

## Problemas Encontrados e Correcoes

Durante a revisao, os testes apontaram um indice duplicado em
`ix_expenses_recurring_key`. A declaracao duplicada foi removida do campo do
modelo, mantendo o indice explicito usado pela migration.

Tambem foi atualizado um teste antigo de modelo para informar `expense_date`,
pois a data da despesa agora e obrigatoria para registros operacionais.
