# Etapa 7 - Compras de Filamentos

## Visao geral

Esta etapa implementou o modulo de compras de filamentos do JOVE Manager.

Cada compra e registrada como historico independente de preco, fornecedor e
custo por grama. O modulo diferencia compra de estoque de consumo efetivo na
producao, deixando o consumo para uma futura etapa de controle de estoque.

## Funcionalidades entregues

- Listagem em `/filament-purchases`.
- Cadastro em `/filament-purchases/new`.
- Consulta em `/filament-purchases/{id}`.
- Edicao em `/filament-purchases/{id}/edit`.
- Filtros por data, material e fornecedor.
- Grafico simples de compras por mes.
- API autenticada em `/api/filament-purchases`.

## Campos

- Marca.
- Material.
- Cor.
- Peso adquirido.
- Valor do material.
- Frete.
- Descontos.
- Custo total.
- Custo por grama.
- Fornecedor.
- Data da compra.
- Observacoes.

## Materiais

- PLA.
- PLA Silk.
- PETG.
- ABS.
- TPU.
- Outros.

## Calculos

```text
Custo total = valor do material + frete - descontos
Custo por grama = custo total / peso adquirido
```

Todos os calculos usam `Decimal`.

## Banco de dados

Migration criada:

```text
migrations/versions/20260922_005_filament_purchases.py
```

Ela cria a tabela `filament_purchases` com indices por data, material/cor e
fornecedor/data.

Comando executado:

```bash
alembic upgrade head
```

Resultado:

```text
20260922_005 (head)
```

## Testes

Arquivo criado:

```text
tests/test_filament_purchases.py
```

Os testes verificam:

- custo total;
- custo por grama;
- desconto reduzindo o total;
- multiplas compras do mesmo filamento preservando historico;
- rejeicao de total negativo;
- criacao via formulario autenticado;
- protecao da API.

Comando executado:

```bash
pytest -p no:cacheprovider
```

Resultado:

```text
41 passed
```

## Arquivos criados

- `app/schemas/filament_purchase.py`
- `app/repositories/filament_purchases.py`
- `app/services/filament_purchases.py`
- `app/routers/filament_purchases.py`
- `app/templates/filament_purchases/list.html`
- `app/templates/filament_purchases/form.html`
- `app/templates/filament_purchases/detail.html`
- `migrations/versions/20260922_005_filament_purchases.py`
- `tests/test_filament_purchases.py`
- `docs/etapa-7-compras-filamentos.md`

## Arquivos modificados

- `app/main.py`
- `app/models/enums.py`
- `app/models/inventory.py`
- `app/models/__init__.py`
- `app/templates/base.html`
- `docs/README.md`

