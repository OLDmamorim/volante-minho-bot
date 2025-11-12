# Bot de Gestão de Pedidos - Hugo

Sistema de gestão de pedidos de apoio às lojas da zona Minho através do Telegram.

## Funcionalidades

### Para Lojas
- Registo automático na primeira utilização
- Criação de pedidos de apoio (Apoio, Férias, Outros)
- Seleção de data através de calendário interativo
- Escolha de período do dia (Manhã, Tarde, Todo o dia)
- Visualização do estado dos pedidos
- Notificações de aprovação/rejeição

### Para Gestores (Hugo e você)
- Visualização de pedidos pendentes
- Aprovação ou rejeição de pedidos com motivo
- Geração automática de ficheiros .ics para calendário
- Links diretos para Google Calendar
- Estatísticas de pedidos
- Notificações de novos pedidos

## Instalação

### 1. Requisitos
- Python 3.9 ou superior
- pip (gestor de pacotes Python)

### 2. Instalar Dependências

```bash
cd hugo_bot
pip install -r requirements.txt
```

### 3. Configurar IDs de Administradores

Antes de executar o bot, é necessário configurar os IDs do Telegram dos administradores.

**Como obter o seu ID do Telegram:**

1. Abra o Telegram e procure pelo bot `@userinfobot`
2. Inicie uma conversa com ele (`/start`)
3. O bot irá responder com o seu ID (um número)
4. Copie esse número

**Configurar no bot:**

Edite o ficheiro `config.py` e substitua a lista `ADMIN_IDS`:

```python
ADMIN_IDS = [
    123456789,  # Substituir pelo seu ID
    987654321,  # Substituir pelo ID do Hugo
]
```

## Execução

Para iniciar o bot:

```bash
cd hugo_bot
python3 main.py
```

O bot ficará em execução e pronto para receber mensagens.

**Nota:** O bot precisa estar em execução continuamente. Para ambientes de produção, recomenda-se:
- Usar um serviço de hospedagem (ex: PythonAnywhere, Heroku, VPS)
- Configurar o bot como serviço systemd (Linux)
- Usar screen ou tmux para manter o processo ativo

## Utilização

### Primeira Vez (Lojas)

1. Abra o Telegram e procure pelo bot (nome definido no BotFather)
2. Envie `/start`
3. O bot irá solicitar o nome da loja
4. Após registar, terá acesso ao menu principal

### Criar Pedido (Loja)

1. No menu principal, selecione "📝 Novo Pedido"
2. Escolha o tipo de pedido (Apoio, Férias, Outros)
3. Selecione a data no calendário
4. Escolha o período (Manhã, Tarde, Todo o dia)
5. Confirme o pedido
6. Aguarde aprovação dos gestores

### Gerir Pedidos (Gestores)

1. Quando um novo pedido é criado, receberá uma notificação
2. Pode aprovar ou rejeitar diretamente da notificação
3. Ao aprovar:
   - A loja é notificada
   - Recebe um ficheiro .ics para adicionar ao calendário
   - Recebe um link para adicionar ao Google Calendar
4. Ao rejeitar:
   - Deve fornecer um motivo
   - A loja é notificada com o motivo

## Estrutura do Projeto

```
hugo_bot/
├── main.py                 # Ficheiro principal do bot
├── config.py              # Configurações e constantes
├── requirements.txt       # Dependências Python
├── README.md             # Esta documentação
├── database/
│   ├── db_manager.py     # Gestor de base de dados
│   └── hugo_bot.db       # Base de dados SQLite (criado automaticamente)
├── handlers/
│   ├── shop_handlers.py  # Handlers para lojas
│   └── admin_handlers.py # Handlers para gestores
└── utils/
    ├── calendar_utils.py # Calendário inline
    └── ics_generator.py  # Gerador de ficheiros .ics
```

## Base de Dados

O bot utiliza SQLite para armazenar dados. A base de dados é criada automaticamente na primeira execução.

### Tabelas

**users**
- Armazena informações de utilizadores (lojas e gestores)

**requests**
- Armazena todos os pedidos criados

**notifications**
- Histórico de notificações enviadas

### Backup

Recomenda-se fazer backup regular do ficheiro `database/hugo_bot.db`.

## Comandos do Bot

### Comandos Gerais
- `/start` - Inicia o bot e regista utilizador
- `/menu` - Volta ao menu principal
- `/help` - Mostra ajuda

## Períodos e Horários

- **Manhã**: 09:00 - 13:00
- **Tarde**: 14:00 - 18:00
- **Todo o dia**: 09:00 - 18:00

Estes horários podem ser ajustados no ficheiro `config.py`.

## Resolução de Problemas

### Bot não responde
- Verificar se o bot está em execução
- Verificar conexão à internet
- Verificar se o token está correto

### Erro ao criar pedido
- Verificar se a base de dados tem permissões de escrita
- Verificar logs do bot para mais detalhes

### Não recebo notificações (Gestor)
- Verificar se o seu ID está na lista `ADMIN_IDS`
- Verificar se iniciou conversa com o bot (`/start`)

### Ficheiro .ics não funciona
- Verificar se a biblioteca `ics` está instalada
- Tentar usar o link do Google Calendar como alternativa

## Suporte

Para questões ou problemas, contacte o administrador do sistema.

## Licença

Este projeto foi desenvolvido para uso interno da organização.
