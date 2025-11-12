# Guia de Deployment - Railway.app

Este guia irá ajudá-lo a fazer o deployment do bot Volante Minho 2.0 para a Railway.app, garantindo que o bot fica ativo 24/7 com a base de dados persistente.

---

## Pré-requisitos

Antes de começar, certifique-se de que tem:

1. **Conta no GitHub** - Necessária para hospedar o código
2. **Conta na Railway** - Gratuita, sem necessidade de cartão de crédito inicialmente
3. **Backup do bot** - Já criado e guardado

---

## Passo 1: Criar Repositório no GitHub

### 1.1 Criar novo repositório

1. Aceda a [github.com](https://github.com) e faça login
2. Clique no botão **"+"** no canto superior direito
3. Selecione **"New repository"**
4. Preencha os dados:
   - **Repository name:** `volante-minho-bot`
   - **Description:** `Bot Telegram para gestão de pedidos - Volante Minho`
   - **Visibilidade:** Escolha **Private** (recomendado) ou Public
   - **NÃO** marque "Initialize this repository with a README"
5. Clique em **"Create repository"**

### 1.2 Copiar o URL do repositório

Após criar, verá uma página com instruções. Copie o URL que aparece, algo como:
```
https://github.com/SEU_USERNAME/volante-minho-bot.git
```

---

## Passo 2: Fazer Upload do Código para o GitHub

### 2.1 No terminal do seu computador

Se estiver a usar o ambiente Manus, execute estes comandos:

```bash
cd /home/ubuntu/hugo_bot

# Adicionar o repositório remoto (substitua pelo seu URL)
git remote add origin https://github.com/SEU_USERNAME/volante-minho-bot.git

# Fazer push do código
git branch -M main
git push -u origin main
```

### 2.2 Autenticação

O GitHub irá pedir as suas credenciais:
- **Username:** O seu username do GitHub
- **Password:** Use um **Personal Access Token** (não a password normal)

**Como criar um Personal Access Token:**

1. No GitHub, vá a **Settings** (canto superior direito, no seu perfil)
2. No menu lateral, clique em **Developer settings** (no final)
3. Clique em **Personal access tokens** → **Tokens (classic)**
4. Clique em **Generate new token** → **Generate new token (classic)**
5. Dê um nome ao token (ex: "Railway Deployment")
6. Marque a checkbox **repo** (dá acesso total aos repositórios)
7. Clique em **Generate token**
8. **COPIE O TOKEN** (só aparece uma vez!)
9. Use este token como password quando o git pedir

### 2.3 Verificar

Após o push, aceda ao seu repositório no GitHub e confirme que os ficheiros estão lá:
- `bot_v2.py`
- `requirements.txt`
- `Procfile`
- `runtime.txt`
- `railway.json`
- Pasta `database/`

---

## Passo 3: Criar Conta na Railway

1. Aceda a [railway.app](https://railway.app)
2. Clique em **"Start a New Project"** ou **"Login"**
3. Escolha **"Login with GitHub"** (recomendado)
4. Autorize a Railway a aceder ao GitHub
5. Complete o registo se necessário

**Nota:** A Railway oferece $5 de crédito gratuito por mês, mais do que suficiente para este bot.

---

## Passo 4: Criar Projeto na Railway

### 4.1 Novo projeto

1. No dashboard da Railway, clique em **"New Project"**
2. Selecione **"Deploy from GitHub repo"**
3. Se for a primeira vez, clique em **"Configure GitHub App"**
4. Autorize a Railway a aceder aos seus repositórios
5. Selecione o repositório **volante-minho-bot**

### 4.2 Aguardar o deploy inicial

A Railway irá:
- Detetar que é um projeto Python
- Instalar as dependências do `requirements.txt`
- Iniciar o bot com o comando do `Procfile`

Este processo demora cerca de 2-3 minutos.

---

## Passo 5: Adicionar Volume Persistente para a Base de Dados

**IMPORTANTE:** Este passo garante que a base de dados não é perdida quando o bot reinicia.

### 5.1 Criar volume

1. No projeto da Railway, clique no serviço do bot
2. Vá ao separador **"Settings"**
3. Procure a secção **"Volumes"**
4. Clique em **"+ New Volume"**
5. Preencha:
   - **Mount Path:** `/app/database`
   - **Name:** `bot-database` (ou outro nome à sua escolha)
6. Clique em **"Add"**

### 5.2 Verificar

O volume foi criado e está montado em `/app/database`. Isto significa que tudo o que o bot guardar nesta pasta será persistente.

---

## Passo 6: Verificar se o Bot Está a Funcionar

### 6.1 Ver logs

1. No dashboard do projeto, clique no serviço
2. Vá ao separador **"Deployments"**
3. Clique no deployment mais recente
4. Veja os **logs** em tempo real

Deverá ver algo como:
```
🤖 Bot Volante Minho 2.0 V2 iniciado!
✅ Comandos configurados no menu do Telegram
Application started
```

### 6.2 Testar no Telegram

1. Abra o Telegram
2. Procure pelo seu bot
3. Envie `/start`
4. O bot deve responder imediatamente

---

## Passo 7: Configurações Adicionais (Opcional)

### 7.1 Mudar o nome do serviço

1. No serviço, vá a **Settings**
2. Em **Service Name**, altere para algo mais descritivo (ex: "volante-minho-bot")

### 7.2 Configurar variáveis de ambiente (se necessário no futuro)

Se quiser mover o token do bot para variáveis de ambiente:

1. No serviço, vá a **Variables**
2. Clique em **"+ New Variable"**
3. Adicione:
   - **Variable Name:** `BOT_TOKEN`
   - **Value:** `8365753572:AAGiZrUoYxxfYlrRWZaIwNGkKiWQ_EzdX78`
4. No código, altere para ler de `os.getenv('BOT_TOKEN')`

---

## Resolução de Problemas

### Bot não inicia

**Verificar logs:**
1. Vá a **Deployments** → Clique no deployment → **View Logs**
2. Procure por erros em vermelho

**Erros comuns:**

**"No module named 'telegram'"**
- O `requirements.txt` não foi lido corretamente
- Solução: Verificar se o ficheiro está na raiz do repositório

**"Connection refused" ou "Network error"**
- Problema de conexão com o Telegram
- Solução: Aguardar alguns minutos e verificar novamente

**"Database is locked"**
- Múltiplas instâncias do bot a tentar aceder à base de dados
- Solução: Garantir que só há um deployment ativo

### Bot responde lentamente

- Verificar os logs para ver se há erros
- A Railway pode estar a hibernar o serviço (no plano gratuito)
- Solução: Upgrade para plano pago ($5/mês) para evitar hibernação

### Base de dados foi perdida

- O volume não foi configurado corretamente
- Solução: Seguir novamente o **Passo 5** e garantir que o mount path é `/app/database`

### Bot parou de funcionar

1. Verificar se o deployment está ativo em **Deployments**
2. Verificar se não excedeu o limite de créditos gratuitos
3. Verificar logs para erros

---

## Manutenção

### Fazer backup da base de dados

A Railway não faz backups automáticos. Para fazer backup manual:

1. No serviço, vá a **Settings** → **Volumes**
2. Clique no volume `bot-database`
3. **Não há opção de download direto**

**Alternativa:** Criar um script que envia a base de dados para um serviço externo (Dropbox, Google Drive, etc.) periodicamente.

### Atualizar o código

Quando fizer alterações ao código:

1. Faça commit no git:
   ```bash
   cd /home/ubuntu/hugo_bot
   git add .
   git commit -m "Descrição das alterações"
   git push
   ```

2. A Railway irá automaticamente detetar as alterações e fazer redeploy

### Monitorizar uso de recursos

1. No dashboard da Railway, veja o separador **"Usage"**
2. Verifique quanto crédito já usou
3. O bot deve usar muito pouco (menos de $1/mês)

---

## Custos

**Plano Gratuito (Hobby):**
- $5 de crédito grátis por mês
- Suficiente para este bot
- Pode hibernar após inatividade

**Plano Developer ($5/mês):**
- $5 de crédito incluído
- Sem hibernação
- Prioridade no suporte

**Estimativa para este bot:**
- Uso de CPU: Muito baixo
- Uso de RAM: ~50-100 MB
- Uso de rede: Mínimo
- **Custo estimado: $0.50 - $2.00/mês**

---

## Checklist Final

Antes de considerar o deployment completo, verifique:

- [ ] Repositório criado no GitHub
- [ ] Código enviado para o GitHub (git push)
- [ ] Projeto criado na Railway
- [ ] Deploy concluído com sucesso
- [ ] Volume persistente criado e montado em `/app/database`
- [ ] Bot responde no Telegram
- [ ] Comandos funcionam corretamente
- [ ] Base de dados está a guardar informações

---

## Contacto e Suporte

Se tiver problemas:

1. Verifique os logs na Railway
2. Consulte a documentação oficial: [docs.railway.app](https://docs.railway.app)
3. Contacte o suporte da Railway (muito responsivos)

---

## Conclusão

Após seguir todos estes passos, o seu bot estará:

✅ Ativo 24 horas por dia, 7 dias por semana
✅ Com base de dados persistente
✅ Acessível a todas as lojas
✅ Pronto para uso em produção

**Parabéns pelo deployment!** 🎉
