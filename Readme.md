# Dashboard de Saúde Ocupacional

Aplicação web em Django para gestão e monitoramento de indicadores de Saúde Ocupacional.

O sistema reúne visão executiva, gestão de funcionários, relatórios e configurações operacionais em uma interface única.

Nome oficial do projeto: Dashboard de Saúde Ocupacional.

## Funcionalidades

- Dashboard modular com abas e métricas calculadas no backend
- Cartões da home com visibilidade por usuário
- Gestão de funcionários com tela própria de edição (fora do admin padrão)
- Indicadores de absenteísmo calculados automaticamente com base em dados reais
- Cards de múltiplos itens em formato de tabela para melhor leitura
- Busca de funcionários insensível a maiúsculas/minúsculas e acentuação
- Tela de configurações com salvamento local no navegador

## Tecnologias

- Python 3
- Django 5.2
- SQLite
- HTML, CSS e JavaScript
- Chart.js
- Vercel (deploy)

## Estrutura do Projeto

- occupational_health: configuração principal do Django
- health: app com views, models, templates, static e admin
- api/index.py: entrada WSGI para deploy no Vercel
- db.sqlite3: base local para desenvolvimento

## Como Rodar Localmente

1. Clonar o repositório
2. Criar e ativar ambiente virtual
3. Instalar dependências
4. Aplicar migrações
5. Iniciar servidor

Comandos (Linux):

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

Aplicação local:

http://127.0.0.1:8000

## Administração

Para acessar o admin do Django:

python manage.py createsuperuser

Depois acesse:

http://127.0.0.1:8000/admin/

## Deploy no Vercel (Django + SQLite)

O projeto está preparado para rodar no Vercel com SQLite em /tmp/db.sqlite3.

### Comportamento no Vercel

- No primeiro cold start, a API tenta copiar db.sqlite3 para /tmp
- Executa collectstatic automaticamente
- Depois executa migrate automaticamente
- Enquanto a instância estiver ativa, leitura e escrita funcionam normalmente

Arquivos estáticos (CSS, JS e imagens) são servidos via WhiteNoise em /static.

### Limitação Importante

No Vercel, o filesystem é efêmero.

Isso significa que dados gravados em SQLite não são persistidos entre novas instâncias, cold starts e deploys.

Para produção com persistência real, use banco gerenciado (PostgreSQL, MySQL, Turso/libSQL etc.).

### Variáveis de Ambiente Recomendadas

- DJANGO_SECRET_KEY
- DJANGO_DEBUG=False
- ALLOWED_HOSTS=.vercel.app
- CSRF_TRUSTED_ORIGINS=https://*.vercel.app
- SQLITE_DB_PATH=/tmp/db.sqlite3
