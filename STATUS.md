# Status do Bot Volante Minho 2.0

**Data:** 10 de Novembro de 2025  
**Versão:** 2.0  
**Estado:** ✅ Ativo e Funcional

---

## Informações do Bot

**Nome:** Volante Minho 2.0  
**Token:** `8365753572:AAGiZrUoYxxfYlrRWZaIwNGkKiWQ_EzdX78`  
**Administradores:**
- ID: 228613920 (M@ster™)
- ID: 615966323 (Hugo Silva)

---

## Funcionalidades Implementadas

### Sistema de Registo
O bot permite que utilizadores se registem fornecendo o nome da sua loja. Após o registo, o utilizador tem acesso a todos os comandos disponíveis para lojas.

### Calendário Visual Interativo
O calendário mostra a disponibilidade dos dias com um sistema de cores intuitivo. Os utilizadores podem navegar entre meses e visualizar rapidamente quais os dias disponíveis ou ocupados. As cores utilizadas são verde para dias disponíveis, vermelho para dias totalmente ocupados, roxo para manhãs ocupadas, azul para tardes ocupadas e amarelo para pedidos pendentes.

### Sistema de Pedidos
As lojas podem criar pedidos de três tipos: Apoio, Férias ou Outros. Para cada pedido, o utilizador seleciona a data através do calendário visual, escolhe o período (Manhã, Tarde ou Todo o dia) e pode adicionar observações opcionais.

### Pedidos de Férias com Intervalo de Datas
Para pedidos de férias, o sistema permite selecionar uma data de início e uma data de fim. O bot cria automaticamente um pedido individual para cada dia do intervalo, facilitando a gestão e visualização no calendário.

### Sistema de Aprovação para Gestores
Os administradores recebem notificações de novos pedidos e podem aprová-los ou rejeitá-los. Ao aprovar, é gerado automaticamente um link para adicionar o evento ao Google Calendar. Ao rejeitar, o gestor deve fornecer um motivo que será comunicado à loja.

### Estatísticas e Relatórios
Os administradores têm acesso a estatísticas completas do sistema, incluindo totais por status, tipo de pedido, período e ranking das lojas com mais pedidos. Existe também uma agenda semanal que mostra os pedidos aprovados para os próximos sete dias.

### Integração com Google Calendar
Quando um pedido é aprovado, o sistema gera automaticamente um link para adicionar o evento ao Google Calendar. O evento inclui o título com o tipo de pedido e período, a data e hora corretas, e uma descrição com as informações da loja e observações.

---

## Comandos Disponíveis

### Para Lojas

**`/start`** - Inicia o bot e regista a loja (primeira utilização) ou mostra o menu principal (utilizadores já registados).

**`/pedido`** - Inicia o processo de criação de um novo pedido. O utilizador escolhe o tipo, seleciona a data no calendário visual, define o período e pode adicionar observações.

**`/calendario`** - Mostra o calendário visual com a disponibilidade dos dias. Permite navegar entre meses para visualizar a ocupação futura.

**`/meus_pedidos`** - Lista os últimos dez pedidos da loja com informações sobre tipo, data, período e status atual (pendente, aprovado ou rejeitado).

**`/minha_loja`** - Apresenta informações da loja incluindo nome, ID do Telegram e estatísticas pessoais (total de pedidos, pendentes e aprovados).

**`/menu`** - Mostra o menu principal com todos os comandos disponíveis para o utilizador.

**`/help`** - Apresenta um guia completo de utilização do bot, incluindo instruções para criar pedidos, legenda do calendário e informações sobre pedidos de férias.

### Para Administradores

**`/pendentes`** - Lista todos os pedidos com status pendente. Para cada pedido, mostra informações completas e botões para aprovar ou rejeitar.

**`/estatisticas`** - Apresenta estatísticas completas do sistema, incluindo totais gerais, distribuição por status, tipo, período e ranking das lojas mais ativas.

**`/agenda_semana`** - Mostra a agenda dos próximos sete dias com todos os pedidos aprovados organizados por data, incluindo dia da semana, loja, tipo e período.

---

## Estrutura da Base de Dados

### Tabela: users
Armazena informações dos utilizadores registados no sistema.

**Colunas:**
- `id` (INTEGER, PRIMARY KEY) - Identificador único do utilizador
- `telegram_id` (INTEGER, UNIQUE) - ID do Telegram do utilizador
- `shop_name` (TEXT) - Nome da loja
- `created_at` (TIMESTAMP) - Data e hora de registo

### Tabela: requests
Armazena todos os pedidos criados pelas lojas.

**Colunas:**
- `id` (INTEGER, PRIMARY KEY) - Identificador único do pedido
- `shop_telegram_id` (INTEGER) - ID do Telegram da loja que criou o pedido
- `request_type` (TEXT) - Tipo do pedido (Apoio, Férias, Outros)
- `start_date` (DATE) - Data do pedido
- `end_date` (DATE) - Data de fim (para pedidos de férias)
- `period` (TEXT) - Período (Manhã, Tarde, Todo o dia)
- `status` (TEXT) - Status do pedido (Pendente, Aprovado, Rejeitado)
- `rejection_reason` (TEXT) - Motivo da rejeição (se aplicável)
- `observations` (TEXT) - Observações adicionadas pelo utilizador
- `created_at` (TIMESTAMP) - Data e hora de criação do pedido
- `processed_at` (TIMESTAMP) - Data e hora de processamento
- `processed_by` (INTEGER) - ID do administrador que processou

---

## Arquivos do Projeto

### Código Principal
- **`bot_v2.py`** - Arquivo principal com toda a lógica do bot
- **`visual_calendar.py`** - Módulo do calendário visual com sistema de cores
- **`calendar_helper.py`** - Funções auxiliares para manipulação de calendário
- **`calendar_links.py`** - Geração de links para Google Calendar

### Base de Dados
- **`database/hugo_bot.db`** - Base de dados SQLite com todas as informações

### Ambiente Virtual
- **`venv/`** - Ambiente virtual Python com dependências instaladas

### Documentação
- **`STATUS.md`** - Este arquivo com o status atual do bot
- **`TESTE.md`** - Lista de verificação para testes

---

## Dependências

O bot utiliza as seguintes bibliotecas Python:

- **python-telegram-bot** - Framework para criação de bots Telegram
- **sqlite3** - Gestão da base de dados (incluído no Python)
- **datetime** - Manipulação de datas e horas (incluído no Python)

---

## Como Executar

### Localmente (Ambiente de Desenvolvimento)

Para executar o bot localmente no ambiente de desenvolvimento:

```bash
cd /home/ubuntu/hugo_bot
source venv/bin/activate
python bot_v2.py
```

O bot ficará ativo enquanto o terminal estiver aberto. Para parar, pressione `Ctrl+C`.

### Em Background (Servidor)

Para executar o bot em background:

```bash
cd /home/ubuntu/hugo_bot
source venv/bin/activate
nohup python bot_v2.py > bot.log 2>&1 &
```

Para verificar se está a correr:

```bash
ps aux | grep bot_v2.py
```

Para parar o bot:

```bash
kill <PID>
```

---

## Próximos Passos Sugeridos

### Deployment em Produção
Para manter o bot ativo vinte e quatro horas por dia, sete dias por semana, recomenda-se fazer deployment numa plataforma de hosting como Railway.app, Heroku ou similar. Estas plataformas oferecem planos gratuitos adequados para bots Telegram.

### Backup Automático
Implementar um sistema de backup automático da base de dados para prevenir perda de informações. O backup pode ser agendado diariamente e enviado para um serviço de armazenamento na nuvem.

### Notificações Avançadas
Adicionar notificações automáticas para lembrar gestores de pedidos pendentes há mais de vinte e quatro horas ou notificar lojas sobre pedidos que estão próximos da data.

### Relatórios Mensais
Implementar geração automática de relatórios mensais com estatísticas detalhadas que podem ser enviados aos gestores.

### Sistema de Permissões
Adicionar diferentes níveis de permissões para permitir múltiplos gestores com diferentes responsabilidades.

---

## Contacto e Suporte

Para questões técnicas ou sugestões de melhorias, contacte os administradores do sistema através do Telegram.

**Última atualização:** 10 de Novembro de 2025, 19:50 UTC
