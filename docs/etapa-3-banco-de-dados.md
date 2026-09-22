# Etapa 3 - Estrutura Inicial do Banco

## Visao geral

Esta etapa criou a estrutura inicial do banco de dados do JOVE Manager usando
SQLAlchemy e Alembic, com SQLite como banco inicial persistente.

As entidades foram modeladas para permitir evolucao das proximas etapas sem
implementar regras financeiras agora.

## Entidades criadas

- Usuarios.
- Clientes.
- Produtos.
- Vendas.
- Itens de venda.
- Compras.
- Itens de compra.
- Filamentos.
- Equipamentos.
- Despesas.
- Categorias financeiras.

## Decisoes tecnicas

- Todos os registros possuem `id` inteiro como identificador unico.
- Todos os registros possuem `created_at` e `updated_at`.
- Valores financeiros usam `Numeric`, mapeado para `Decimal` no Python.
- Nenhum campo financeiro usa `float`.
- Vendas possuem relacionamento um-para-muitos com itens de venda.
- Compras possuem relacionamento um-para-muitos com itens de compra.
- Itens de compra podem referenciar filamentos ou equipamentos.
- Categorias financeiras diferenciam receitas, custos de producao, despesas
  operacionais, investimentos em equipamentos e compras de estoque.
- Indices foram criados para consultas frequentes por status, data, categoria,
  cliente, fornecedor, material e cor.

## Migration

Migration inicial criada em:

```text
migrations/versions/20260922_001_initial_business_schema.py
```

Ela cria tabelas e indices sem apagar dados existentes.

Comando executado:

```bash
alembic upgrade head
```

Resultado:

```text
Migration aplicada com sucesso no SQLite.
```

## Testes

Arquivo criado:

```text
tests/test_models.py
```

Os testes verificam:

- venda com varios produtos;
- compra com filamentos e equipamento;
- categorias financeiras para os fluxos principais;
- despesa vinculada a categoria financeira;
- ausencia de colunas `Float` nos modelos.

Comando executado:

```bash
pytest
```

Resultado:

```text
11 passed
```

Aviso observado:

```text
Pytest nao conseguiu criar cache em .pytest_cache por permissao do ambiente.
```

Esse aviso nao impediu a execucao dos testes.

## Arquivos criados

- `app/models/enums.py`
- `app/models/mixins.py`
- `app/models/user.py`
- `app/models/client.py`
- `app/models/product.py`
- `app/models/inventory.py`
- `app/models/finance.py`
- `app/models/sale.py`
- `app/models/purchase.py`
- `migrations/versions/20260922_001_initial_business_schema.py`
- `tests/test_models.py`
- `docs/etapa-3-banco-de-dados.md`

## Arquivos modificados

- `app/models/__init__.py`
- `docs/README.md`

