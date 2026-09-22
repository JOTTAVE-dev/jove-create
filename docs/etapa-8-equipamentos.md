# Etapa 8 - Ferramentas e Equipamentos

## Visao geral

Esta etapa implementou o modulo de gerenciamento de ferramentas e equipamentos
do JOVE Manager.

O modulo controla investimentos realizados pela JOVE CREATE, separando
equipamentos duraveis de materiais consumiveis e mantendo manutencoes em
registro proprio.

## Funcionalidades entregues

- Listagem em `/equipments`.
- Cadastro em `/equipments/new`.
- Consulta em `/equipments/{id}`.
- Edicao em `/equipments/{id}/edit`.
- Filtro por categoria.
- Visualizacao do total investido.
- Registro de manutencao.
- API autenticada em `/api/equipments`.

## Campos

- Nome.
- Categoria.
- Tipo: duravel ou consumivel.
- Fabricante.
- Modelo.
- Data da compra.
- Valor.
- Fornecedor.
- Vida util estimada.
- Observacoes.
- Status.

## Regras atendidas

- Diferencia equipamentos duraveis de materiais consumiveis.
- O valor do equipamento e registrado como investimento, nao como custo
  automatico de producao do mes.
- Manutencoes ficam separadas do valor de compra.
- A vida util estimada prepara a base para depreciacao futura por hora de uso.

## Banco de dados

Migration criada:

```text
migrations/versions/20260922_006_equipment_management.py
```

Ela expande `equipments` e cria `equipment_maintenances`.

Resultado:

```text
20260922_006 (head)
```

## Testes

Arquivo criado:

```text
tests/test_equipments.py
```

Os testes verificam:

- investimento separado de custo de producao;
- suporte a item consumivel;
- registro de manutencao;
- filtro por categoria;
- criacao via formulario autenticado;
- protecao da API.

Resultado:

```text
47 passed
```

## Arquivos criados

- `app/schemas/equipment.py`
- `app/repositories/equipments.py`
- `app/services/equipments.py`
- `app/routers/equipments.py`
- `app/templates/equipments/list.html`
- `app/templates/equipments/form.html`
- `app/templates/equipments/detail.html`
- `migrations/versions/20260922_006_equipment_management.py`
- `tests/test_equipments.py`
- `docs/etapa-8-equipamentos.md`

## Arquivos modificados

- `app/main.py`
- `app/models/enums.py`
- `app/models/inventory.py`
- `app/models/__init__.py`
- `app/templates/base.html`
- `docs/README.md`

