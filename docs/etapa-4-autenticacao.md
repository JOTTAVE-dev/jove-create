# Etapa 4 - Autenticacao e Seguranca

## Visao geral

Esta etapa implementou o sistema inicial de autenticacao do JOVE Manager.

O sistema agora possui login, logout, protecao de paginas privadas, protecao de
rotas de API, sessoes persistidas no banco, alteracao de senha, CSRF em
formularios autenticados e protecao contra tentativas excessivas de login.

Nao foi implementado cadastro publico de usuarios.

## Funcionalidades

- Login em `/login`.
- Logout via `POST /logout`.
- Dashboard privado em `/`.
- API autenticada em `/api/me`.
- Alteracao de senha em `/settings/password`.
- Bootstrap opcional de administrador inicial via variaveis de ambiente.

## Seguranca

- Senhas armazenadas com PBKDF2-HMAC-SHA256, salt unico e multiplas iteracoes.
- Cookie de sessao `HttpOnly`.
- Cookie marcado como `Secure` automaticamente quando a requisicao usa HTTPS.
- `SameSite=Lax`.
- Sessao server-side em `auth_sessions`.
- Cookie guarda apenas token aleatorio.
- Banco guarda apenas hash do token de sessao.
- CSRF validado por token associado a sessao.
- Mensagens de login genericas para nao revelar existencia de usuario.
- Rate limit inicial em memoria contra tentativas excessivas de login.
- Credenciais iniciais via variaveis de ambiente, nao hardcoded.

## Variaveis de ambiente

```text
ADMIN_EMAIL=admin@jove.local
ADMIN_PASSWORD=change-this-admin-password
SESSION_COOKIE_NAME=jove_session
CSRF_COOKIE_NAME=jove_csrf
SESSION_EXPIRE_MINUTES=480
LOGIN_MAX_ATTEMPTS=5
LOGIN_LOCKOUT_MINUTES=15
```

O administrador inicial so e criado automaticamente se `ADMIN_EMAIL` e
`ADMIN_PASSWORD` estiverem configurados e se ainda nao existir usuario no banco.

## Banco de dados

Migration criada:

```text
migrations/versions/20260922_002_authentication.py
```

Ela adiciona:

- `role` em `users`;
- `password_changed_at` em `users`;
- tabela `auth_sessions`.

Comando executado:

```bash
alembic upgrade head
```

Resultado:

```text
20260922_002 (head)
```

## Testes

Arquivo criado:

```text
tests/test_auth.py
```

Os testes verificam:

- hash de senha sem texto puro;
- login com cookie HttpOnly;
- dashboard privado;
- acesso autenticado ao dashboard;
- API protegida;
- API autenticada retornando usuario atual;
- mensagem generica de erro de login;
- bloqueio por tentativas excessivas;
- CSRF obrigatorio para alteracao de senha;
- alteracao de senha com sucesso.

Comando executado:

```bash
pytest -p no:cacheprovider
```

Resultado:

```text
21 passed
```

## Arquivos criados

- `app/core/auth.py`
- `app/core/passwords.py`
- `app/core/tokens.py`
- `app/models/auth.py`
- `app/routers/auth.py`
- `app/routers/api.py`
- `app/services/auth.py`
- `app/services/bootstrap.py`
- `app/templates/login.html`
- `app/templates/change_password.html`
- `migrations/versions/20260922_002_authentication.py`
- `tests/test_auth.py`
- `docs/etapa-4-autenticacao.md`

## Arquivos modificados

- `.env.example`
- `.gitignore`
- `app/core/config.py`
- `app/core/errors.py`
- `app/main.py`
- `app/models/__init__.py`
- `app/models/user.py`
- `app/routers/home.py`
- `app/templates/base.html`
- `app/static/css/main.css`
- `tests/test_app.py`
- `docs/README.md`

