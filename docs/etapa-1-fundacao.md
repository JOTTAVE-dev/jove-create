# Etapa 1 - Fundacao do Projeto

## Visao geral

O JOVE Manager e um Web App para gerenciamento financeiro e comercial da
JOVE CREATE, uma pequena empresa de impressao 3D.

Nesta primeira etapa foi criada apenas a fundacao tecnica do sistema. Ainda nao
foram implementadas funcionalidades comerciais como clientes, produtos, vendas,
despesas, receitas, dashboard financeiro ou autenticacao.

O objetivo desta etapa foi preparar uma base organizada, modular, responsiva e
pronta para evoluir nas proximas fases.

## Tecnologias configuradas

- Python 3.12+
- FastAPI
- SQLAlchemy
- Pydantic
- Pydantic Settings
- Alembic
- Jinja2
- HTML5
- CSS3
- JavaScript
- SQLite
- Docker
- Docker Compose
- Pytest

## Estrutura criada

```text
app/
├── main.py
├── core/
├── models/
├── schemas/
├── routers/
├── repositories/
├── services/
├── templates/
└── static/

migrations/
tests/
docs/
requirements.txt
Dockerfile
docker-compose.yml
.env.example
.gitignore
alembic.ini
README.md
```

## Organizacao da aplicacao

### `app/main.py`

Arquivo principal da aplicacao FastAPI.

Ele cria a aplicacao, registra as rotas, monta os arquivos estaticos e registra
os tratadores de erro.

Atualmente a aplicacao possui:

- rota web inicial em `/`;
- rota de saude em `/health`;
- arquivos estaticos servidos por `/static`;
- suporte a templates Jinja2.

### `app/core/`

Contem configuracoes e utilitarios compartilhados.

Arquivos principais:

- `config.py`: configuracoes via variaveis de ambiente.
- `currency.py`: formatacao de valores em reais brasileiros.
- `timezone.py`: suporte ao fuso horario `America/Fortaleza`.
- `errors.py`: tratamento padronizado de erros HTTP e validacao.
- `security.py`: reservado para a futura etapa de seguranca e autenticacao.

Configuracoes iniciais:

```text
APP_NAME=JOVE Manager
APP_TIMEZONE=America/Fortaleza
DATABASE_URL=sqlite:///./data/jove.db
SECRET_KEY=change-this-secret-key-before-production
```

### `app/core/database.py`

Contem a configuracao de banco de dados.

Este arquivo concentra a base declarativa do SQLAlchemy, a engine, a session
factory e a dependencia `get_db`.

O banco inicial e SQLite, mas a configuracao por `DATABASE_URL` permite migrar
para PostgreSQL futuramente sem alterar a arquitetura principal.

A pasta `app/db/` foi mantida como compatibilidade interna, reexportando os
objetos definidos em `app/core/database.py`.

### `app/models/`

Reservado para os modelos SQLAlchemy.

Nesta etapa nao foram criadas tabelas comerciais, pois o plano definiu que a
fundacao nao deve antecipar funcionalidades ainda nao solicitadas.

### `app/schemas/`

Contem schemas Pydantic.

Nesta etapa foi criado o schema:

- `HealthResponse`, usado pela rota `/health`.

### `app/repositories/`

Reservado para acesso ao banco de dados.

Esta camada sera usada nas proximas etapas para concentrar consultas e comandos
de persistencia, evitando que as rotas HTTP acessem o banco diretamente.

### `app/services/`

Reservado para regras de negocio.

Esta camada sera usada para calculos, validacoes comerciais, regras financeiras
e fluxos da aplicacao.

### `app/routers/`

Contem as rotas da aplicacao.

Nesta etapa foi criada:

```text
GET /health
```

Resposta esperada:

```json
{
  "status": "ok",
  "app_name": "JOVE Manager",
  "timezone": "America/Fortaleza"
}
```

Tambem foi criada:

```text
GET /
```

Essa rota renderiza a pagina inicial do sistema.

As pastas antigas `app/api/` e `app/web/` foram mantidas como compatibilidade,
mas as rotas ativas ficam em `app/routers/`.

### `app/templates/`

Contem os templates HTML.

Arquivos criados:

- `base.html`: estrutura HTML base, cabecalho, CSS, manifest e JavaScript.
- `index.html`: pagina inicial da fundacao do sistema.

### `app/static/`

Contem arquivos estaticos do frontend.

Arquivos criados:

- `css/main.css`: estilo responsivo mobile-first.
- `js/app.js`: registro do service worker.
- `manifest.json`: manifest PWA.
- `sw.js`: service worker inicial.
- `images/icon.svg`: icone inicial da aplicacao.

## Interface inicial

A interface foi criada com direcao visual operacional moderna:

- layout limpo;
- responsivo;
- mobile-first;
- foco em uso diario;
- cores profissionais com presenca da identidade JOVE;
- exibicao de moeda em BRL;
- exibicao de data local.

Esta tela ainda nao e um dashboard funcional. Ela e apenas a tela inicial da
fundacao do sistema.

## PWA

O projeto ja possui preparacao inicial para PWA:

- `manifest.json`;
- `sw.js`;
- icone SVG;
- `theme-color`;
- registro do service worker via JavaScript.

Essa configuracao permite evoluir futuramente para instalacao em celular e
computador.

## Alembic e migrations

O Alembic foi configurado desde o inicio.

Arquivos principais:

- `alembic.ini`;
- `migrations/env.py`;
- `migrations/script.py.mako`;
- `migrations/versions/.gitkeep`.

Como ainda nao existem tabelas de negocio, nao foi criada uma migration com
modelos comerciais.

O `alembic.ini` aponta para `migrations/` como pasta ativa de migrations.

Comandos futuros:

```bash
alembic revision --autogenerate -m "mensagem"
alembic upgrade head
```

## Docker

Foram criados:

- `Dockerfile`;
- `docker-compose.yml`.

Execucao com Docker:

```bash
docker compose up --build
```

O container sobe a aplicacao em:

```text
http://127.0.0.1:8000
```

O arquivo `docker-compose.yml` tambem cria um volume local para persistir o
banco SQLite em `./data`.

## Testes

Foi criada uma suite inicial em:

```text
tests/test_app.py
```

Os testes previstos verificam:

- se `/health` retorna sucesso;
- se `/` renderiza a pagina inicial;
- se o timezone padrao e `America/Fortaleza`;
- se valores sao formatados corretamente em BRL;
- se `DATABASE_URL` e configuravel;
- se a aplicacao nao depende de PostgreSQL nesta etapa.

Comando:

```bash
pytest
```

## Validacao feita nesta etapa

Foi executada uma validacao de compilacao Python:

```bash
python -m compileall app tests
```

Resultado:

```text
Passou sem erros.
```

## Problema encontrado

Nao foi possivel executar `pytest` neste ambiente porque as dependencias ainda
nao estavam instaladas.

A tentativa de instalar com:

```bash
python -m pip install -r requirements.txt
```

falhou por restricao de acesso ao indice de pacotes no sandbox. A permissao para
repetir a instalacao fora do sandbox foi recusada.

Assim que as dependencias forem instaladas, a suite podera ser executada com:

```bash
pytest
```

## Como executar localmente

Criar ambiente virtual:

```bash
python -m venv .venv
```

Ativar no Windows:

```bash
.venv\Scripts\activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Subir o servidor:

```bash
uvicorn app.main:app --reload
```

Acessar:

```text
http://127.0.0.1:8000
```

## Arquivos criados na etapa

- `requirements.txt`
- `.env.example`
- `.gitignore`
- `Dockerfile`
- `docker-compose.yml`
- `README.md`
- `alembic.ini`
- `migrations/env.py`
- `migrations/script.py.mako`
- `migrations/versions/.gitkeep`
- `app/__init__.py`
- `app/main.py`
- `app/core/__init__.py`
- `app/core/config.py`
- `app/core/database.py`
- `app/core/currency.py`
- `app/core/errors.py`
- `app/core/security.py`
- `app/core/timezone.py`
- `app/db/__init__.py`
- `app/db/base.py`
- `app/db/session.py`
- `app/models/__init__.py`
- `app/schemas/__init__.py`
- `app/schemas/health.py`
- `app/repositories/__init__.py`
- `app/services/__init__.py`
- `app/routers/__init__.py`
- `app/routers/health.py`
- `app/routers/home.py`
- `app/api/__init__.py`
- `app/api/routes/__init__.py`
- `app/api/routes/health.py`
- `app/web/__init__.py`
- `app/web/routes/__init__.py`
- `app/web/routes/home.py`
- `app/templates/base.html`
- `app/templates/index.html`
- `app/static/css/main.css`
- `app/static/js/app.js`
- `app/static/manifest.json`
- `app/static/sw.js`
- `app/static/img/icon.svg`
- `app/static/images/.gitkeep`
- `app/static/images/icon.svg`
- `tests/__init__.py`
- `tests/test_app.py`
- `docs/README.md`
- `docs/etapa-1-fundacao.md`

## Arquivos modificados na etapa

Nenhum arquivo preexistente foi modificado, pois o projeto estava vazio antes da
implementacao da fundacao.

## Proximas etapas recomendadas

### Etapa 2 - Seguranca e usuarios

- login;
- senha com hash seguro;
- sessoes protegidas;
- usuario administrador inicial;
- protecao de rotas internas.

### Etapa 3 - Cadastros comerciais

- clientes;
- produtos;
- categorias.

### Etapa 4 - Custos e precificacao

- custos de material;
- tempo de impressao;
- margem;
- preco de venda;
- calculos com `Decimal`.

### Etapa 5 - Vendas

- pedidos;
- itens;
- status;
- forma de pagamento.

### Etapa 6 - Financeiro

- receitas;
- despesas;
- fluxo de caixa;
- filtros por periodo.

### Etapa 7 - Dashboard

- resumo financeiro;
- vendas recentes;
- indicadores mensais.
