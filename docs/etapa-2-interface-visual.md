# Etapa 2 - Interface Visual

## Visao geral

Esta etapa desenvolveu a interface visual inicial do JOVE Manager para a marca
JOVE CREATE, mantendo o sistema sem regras financeiras reais.

A tela usa dados demonstrativos temporarios apenas para validar layout,
componentes, responsividade e identidade visual. A conexao com dados reais sera
feita em etapas futuras.

## Identidade visual aplicada

As cores foram centralizadas em variaveis CSS no arquivo
`app/static/css/main.css`.

Paleta configurada:

- Marrom principal: `#795548`
- Marrom escuro: `#4E342E`
- Bege: `#F5EFEA`
- Branco: `#FFFFFF`
- Verde: `#388E3C`
- Vermelho: `#D32F2F`

O estilo visual segue a direcao:

- minimalista;
- moderno;
- elegante;
- profissional;
- adequado para uso diario em gestao comercial e financeira.

## Layout responsivo

### Celular

- Navegacao inferior fixa.
- Botao flutuante para adicionar venda.
- Dashboard em cartoes empilhados.
- Formularios em coluna unica.
- Botoes grandes e acessiveis.
- Tabelas com rolagem horizontal quando necessario.

### Computador

- Menu lateral fixo.
- Dashboard em grade.
- Conteudo aproveitando melhor a largura da tela.
- Tabela de vendas completa.
- Paineis organizados em duas colunas.

## Telas iniciais representadas

A interface inicial apresenta secoes para:

- Dashboard.
- Vendas.
- Compras.
- Despesas.
- Relatorios.
- Configuracoes.

Estas secoes estao na pagina inicial e sao acessadas por navegacao com ancora.

## Componentes criados

Foram criados estilos reutilizaveis para:

- botoes;
- cartoes;
- formularios;
- modal demonstrativo;
- tabelas;
- alertas;
- badges;
- indicadores financeiros;
- listas operacionais;
- barras visuais de relatorio.

## Arquivos modificados

- `app/routers/home.py`
- `app/templates/base.html`
- `app/templates/index.html`
- `app/static/css/main.css`
- `app/static/manifest.json`
- `app/static/images/icon.svg`
- `app/static/img/icon.svg`
- `docs/README.md`

## Arquivos criados

- `docs/etapa-2-interface-visual.md`

## Validacao

Foi executado:

```bash
python -m compileall app tests migrations
```

Resultado:

```text
Passou sem erros.
```

Tambem foi tentado:

```bash
pytest
```

O comando nao executou porque `pytest` ainda nao esta instalado no ambiente.

## Observacao importante

Nenhuma funcionalidade financeira real foi implementada nesta etapa. Os valores,
vendas, compras e despesas exibidos sao apenas demonstrativos.

