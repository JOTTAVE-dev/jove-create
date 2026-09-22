# Etapa 5 - Gerenciamento de Produtos

## Visao geral

Esta etapa implementou o modulo inicial de gerenciamento de produtos do JOVE
Manager.

O modulo permite cadastrar, editar, consultar, pesquisar e desativar produtos.
Produtos nao sao excluidos permanentemente, preservando historico e preparando o
sistema para vendas futuras.

## Funcionalidades entregues

- Listagem de produtos em `/products`.
- Cadastro em `/products/new`.
- Consulta em `/products/{id}`.
- Edicao em `/products/{id}/edit`.
- Desativacao via `POST /products/{id}/deactivate`.
- Pesquisa por nome, categoria ou descricao.
- Filtro para incluir produtos inativos.
- API autenticada em `/api/products`.
- API autenticada de consulta em `/api/products/{id}`.

## Campos do produto

- Nome.
- Descricao.
- Categoria.
- Preco de venda opcional.
- Custo estimado de producao.
- Tempo estimado de impressao em minutos.
- Peso estimado em gramas.
- URL de imagem.
- Produto personalizavel.
- Status ativo/inativo.

## Regras atendidas

- Produtos personalizados sao permitidos.
- Preco fixo nao e obrigatorio.
- Valores monetarios usam `Decimal`/`Numeric`, nao `float`.
- Produtos associados a vendas devem ser preservados; a acao disponivel e
  desativacao.
- Campos de custo, tempo e peso deixam o modulo preparado para uma futura
  calculadora de custos de impressao 3D.
- Formularios autenticados usam CSRF.
- Paginas e API exigem autenticacao.

## Arquitetura

Foram usadas camadas separadas:

- `app/schemas/product.py` para validacoes.
- `app/repositories/products.py` para consultas e persistencia.
- `app/services/products.py` para regras do modulo.
- `app/routers/products.py` para rotas web e API.
- `app/templates/products/` para interface.

## Banco de dados

Migration criada:

```text
migrations/versions/20260922_003_products_module.py
```

Ela adiciona campos ao modelo de produtos e cria indice por status/categoria.
A migration preserva dados existentes.

Comando executado:

```bash
alembic upgrade head
```

Resultado:

```text
20260922_003 (head)
```

## Testes

Arquivo criado:

```text
tests/test_products.py
```

Os testes verificam:

- produto personalizado sem preco fixo;
- rejeicao de valores negativos;
- cadastro, pesquisa e desativacao;
- protecao da pagina de produtos;
- criacao via formulario autenticado;
- protecao da API de produtos.

Comando executado:

```bash
pytest -p no:cacheprovider
```

Resultado:

```text
27 passed
```

## Arquivos criados

- `app/schemas/product.py`
- `app/repositories/products.py`
- `app/services/products.py`
- `app/routers/products.py`
- `app/templates/products/list.html`
- `app/templates/products/form.html`
- `app/templates/products/detail.html`
- `migrations/versions/20260922_003_products_module.py`
- `tests/test_products.py`
- `docs/etapa-5-produtos.md`

## Arquivos modificados

- `app/main.py`
- `app/models/product.py`
- `app/templates/base.html`
- `app/static/css/main.css`
- `docs/README.md`

