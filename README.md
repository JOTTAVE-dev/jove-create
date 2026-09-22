# JOVE Manager

Web App modular para gerenciamento financeiro e comercial da JOVE CREATE.

O projeto ja possui a fundacao da aplicacao, autenticacao, interface visual,
dashboard financeiro real, relatorios com exportacao CSV e modulos iniciais
para produtos, vendas, compras de filamentos, equipamentos e despesas
operacionais.

## Estrutura

```text
app/
├── main.py
├── core/
│   ├── config.py
│   ├── database.py
│   └── security.py
├── models/
├── schemas/
├── routers/
├── services/
├── repositories/
├── templates/
└── static/
    ├── css/
    ├── js/
    └── images/

migrations/
tests/
requirements.txt
Dockerfile
docker-compose.yml
.env.example
.gitignore
README.md
```

## Requisitos

- Python 3.12+
- Docker e Docker Compose, opcional para execucao conteinerizada

## Configuracao

Copie o arquivo de exemplo:

```bash
copy .env.example .env
```

Variaveis principais:

- `APP_NAME`, padrao `JOVE Manager`
- `APP_TIMEZONE`, padrao `America/Fortaleza`
- `DATABASE_URL`, padrao `sqlite:///./data/jove.db`
- `SECRET_KEY`, altere antes de qualquer ambiente real
- `ADMIN_EMAIL`, e-mail do administrador inicial
- `ADMIN_PASSWORD`, senha do administrador inicial
- `SESSION_COOKIE_NAME`, nome do cookie de sessao
- `CSRF_COOKIE_NAME`, nome do cookie de CSRF

O banco SQLite fica em `data/jove.db`, mantendo persistencia local. Com Docker,
a pasta `./data` e montada no container para preservar o banco entre reinicios.

## Executar localmente

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Acesse:

```text
http://127.0.0.1:8000
```

Dashboard financeiro:

```text
http://127.0.0.1:8000
```

Rota de verificacao:

```text
http://127.0.0.1:8000/health
```

Modulo de produtos:

```text
http://127.0.0.1:8000/products
```

Modulo de vendas:

```text
http://127.0.0.1:8000/sales
```

Modulo de compras de filamentos:

```text
http://127.0.0.1:8000/filament-purchases
```

Modulo de ferramentas e equipamentos:

```text
http://127.0.0.1:8000/equipments
```

Modulo de despesas:

```text
http://127.0.0.1:8000/expenses
```

Relatorios financeiros:

```text
http://127.0.0.1:8000/reports
```

## Deploy

O projeto esta preparado para:

- PostgreSQL/Supabase via `DATABASE_URL`;
- Vercel com `api/index.py` e `vercel.json`;
- GitHub usando Git.

Veja o passo a passo em:

```text
docs/deploy-supabase-vercel-github.md
```

Antes do primeiro acesso autenticado, aplique as migrations:

```bash
alembic upgrade head
```

Se `ADMIN_EMAIL` e `ADMIN_PASSWORD` estiverem configurados, o primeiro
administrador sera criado automaticamente na inicializacao do app.

## Executar com Docker

```bash
docker compose up --build
```

## Migrations

Criar uma migration:

```bash
alembic revision --autogenerate -m "mensagem"
```

Aplicar migrations:

```bash
alembic upgrade head
```

As migrations ativas ficam na pasta `migrations/`.

## Testes

```bash
pytest
```

Em ambientes onde o cache do Pytest nao puder ser criado, use:

```bash
pytest -p no:cacheprovider
```
