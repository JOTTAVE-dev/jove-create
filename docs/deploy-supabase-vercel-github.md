# Deploy - Supabase, Vercel e GitHub

## Objetivo

Este documento registra a preparacao do JOVE Manager para usar PostgreSQL no
Supabase, deploy na Vercel e versionamento no GitHub.

## Supabase

O projeto usa SQLAlchemy e Alembic. Para producao, configure `DATABASE_URL`
com a string PostgreSQL do Supabase.

Recomendado para Vercel/serverless: usar o pooler em transaction mode, pois
funcoes serverless abrem conexoes curtas.

Exemplo:

```text
DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@[POOLER-HOST]:6543/postgres?sslmode=require
```

Tambem configure:

```text
DATABASE_POOL_SIZE=1
DATABASE_MAX_OVERFLOW=0
```

Depois aplique as migrations no banco remoto:

```bash
alembic upgrade head
```

## Vercel

Arquivos adicionados:

- `api/index.py`
- `vercel.json`

O arquivo `api/index.py` exporta a instancia `app` do FastAPI. A Vercel detecta
essa entrada como uma Function Python.

Variaveis obrigatorias na Vercel:

```text
APP_NAME=JOVE Manager
APP_TIMEZONE=America/Fortaleza
DATABASE_URL=postgresql://...
DATABASE_POOL_SIZE=1
DATABASE_MAX_OVERFLOW=0
SECRET_KEY=...
ADMIN_EMAIL=...
ADMIN_PASSWORD=...
SESSION_COOKIE_NAME=jove_session
CSRF_COOKIE_NAME=jove_csrf
SESSION_EXPIRE_MINUTES=480
LOGIN_MAX_ATTEMPTS=5
LOGIN_LOCKOUT_MINUTES=15
```

Com a Vercel CLI instalada e autenticada:

```bash
vercel
vercel env add DATABASE_URL production
vercel env add SECRET_KEY production
vercel --prod
```

## GitHub

Inicializar o repositório local:

```bash
git init
git add .
git commit -m "Initial JOVE Manager implementation"
```

Depois crie o repositório no GitHub e conecte o remoto:

```bash
git remote add origin https://github.com/SEU_USUARIO/jove-manager.git
git branch -M main
git push -u origin main
```

## Observacoes de Seguranca

- Nunca subir `.env`, `.env.local` ou `.vercel/`.
- Usar `SECRET_KEY` forte em producao.
- Trocar `ADMIN_PASSWORD` apos o primeiro deploy.
- Usar a connection string copiada do painel do Supabase, sem tentar montar o
  host manualmente.
