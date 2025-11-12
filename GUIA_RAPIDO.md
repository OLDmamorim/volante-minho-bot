# Guia de Início Rápido - Bot Hugo

## Passo 1: Obter os IDs do Telegram

Antes de iniciar o bot principal, é necessário obter os IDs do Telegram dos administradores.

### Como obter o ID:

**Opção A - Usando o script auxiliar:**

1. Abra um terminal e execute:
```bash
cd /home/ubuntu/hugo_bot
source venv/bin/activate
python get_my_id.py
```

2. Abra o Telegram e procure pelo bot (o nome que definiu no BotFather)

3. Envie qualquer mensagem ao bot

4. O seu ID será mostrado no terminal e no Telegram

5. Copie o ID e pressione `Ctrl+C` para parar o script

**Opção B - Usando o @userinfobot:**

1. Abra o Telegram e procure por `@userinfobot`

2. Inicie uma conversa com `/start`

3. O bot responderá com o seu ID

4. Copie o ID

### Repetir para o Hugo:

Peça ao Hugo para fazer o mesmo processo e obter o ID dele.

## Passo 2: Configurar os IDs no Bot

1. Abra o ficheiro `config.py`:
```bash
nano /home/ubuntu/hugo_bot/config.py
```

2. Encontre a linha com `ADMIN_IDS = [`

3. Substitua pelos IDs reais:
```python
ADMIN_IDS = [
    123456789,  # Substituir pelo seu ID
    987654321,  # Substituir pelo ID do Hugo
]
```

4. Guarde o ficheiro (`Ctrl+O`, `Enter`, `Ctrl+X`)

## Passo 3: Iniciar o Bot

Execute o script de inicialização:

```bash
cd /home/ubuntu/hugo_bot
./run_bot.sh
```

Ou manualmente:

```bash
cd /home/ubuntu/hugo_bot
source venv/bin/activate
python main.py
```

Verá a mensagem:
```
🤖 Bot iniciado com sucesso!
📊 Base de dados: database/hugo_bot.db
👥 Administradores: 2
```

## Passo 4: Testar o Bot

### Como Loja:

1. Abra o Telegram e procure pelo bot

2. Envie `/start`

3. O bot pedirá o nome da loja

4. Após registar, terá acesso ao menu:
   - 📝 Novo Pedido
   - 📋 Meus Pedidos
   - ℹ️ Ajuda

5. Crie um pedido de teste:
   - Selecione "Novo Pedido"
   - Escolha o tipo (ex: Apoio)
   - Selecione uma data no calendário
   - Escolha o período (ex: Manhã)
   - Confirme

### Como Gestor:

1. Envie `/start` ao bot

2. Verá o menu de administrador:
   - 🔔 Pedidos Pendentes
   - 📊 Todos os Pedidos
   - ℹ️ Ajuda

3. Quando uma loja criar um pedido, receberá uma notificação

4. Pode aprovar ou rejeitar diretamente da notificação

5. Ao aprovar:
   - Receberá um ficheiro `.ics` para adicionar ao calendário
   - Receberá um link para Google Calendar

## Passo 5: Manter o Bot em Execução

### Opção A - Screen (Recomendado para testes):

```bash
# Criar sessão screen
screen -S hugo_bot

# Iniciar o bot
cd /home/ubuntu/hugo_bot
./run_bot.sh

# Desanexar da sessão (Ctrl+A, depois D)
# O bot continuará a correr em background

# Para voltar à sessão:
screen -r hugo_bot
```

### Opção B - Serviço Systemd (Recomendado para produção):

1. Criar ficheiro de serviço:
```bash
sudo nano /etc/systemd/system/hugo_bot.service
```

2. Adicionar conteúdo:
```ini
[Unit]
Description=Bot Hugo - Gestão de Pedidos
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/hugo_bot
ExecStart=/home/ubuntu/hugo_bot/venv/bin/python /home/ubuntu/hugo_bot/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. Ativar e iniciar o serviço:
```bash
sudo systemctl daemon-reload
sudo systemctl enable hugo_bot
sudo systemctl start hugo_bot
```

4. Verificar estado:
```bash
sudo systemctl status hugo_bot
```

5. Ver logs:
```bash
sudo journalctl -u hugo_bot -f
```

## Comandos Úteis

### Parar o bot:
- Se estiver em execução direta: `Ctrl+C`
- Se for serviço: `sudo systemctl stop hugo_bot`

### Ver logs em tempo real:
```bash
# Se for serviço
sudo journalctl -u hugo_bot -f

# Se usar screen
screen -r hugo_bot
```

### Reiniciar o bot:
```bash
# Se for serviço
sudo systemctl restart hugo_bot
```

### Fazer backup da base de dados:
```bash
cp /home/ubuntu/hugo_bot/database/hugo_bot.db /home/ubuntu/hugo_bot_backup_$(date +%Y%m%d).db
```

## Resolução Rápida de Problemas

### Bot não responde:
1. Verificar se está em execução
2. Verificar logs para erros
3. Verificar conexão à internet

### "Erro: Token inválido":
- Verificar se o token no `config.py` está correto

### "Não sou administrador":
- Verificar se o seu ID está em `ADMIN_IDS`
- Reiniciar o bot após alterar configurações

### Ficheiro .ics não funciona:
- Usar o link do Google Calendar como alternativa
- Verificar se a biblioteca `ics` está instalada

## Contacto

Para questões ou problemas, contacte o administrador do sistema.
