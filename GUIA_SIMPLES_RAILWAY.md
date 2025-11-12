# Guia Rápido - Deployment Railway (Via Web)

Este é o guia mais simples possível para colocar o bot online em 10 minutos.

---

## Passo 1: Preparar o Código no GitHub

Tem duas opções:

### Opção A: Usar GitHub Desktop (Mais Fácil)

1. Descarregue o **GitHub Desktop**: https://desktop.github.com
2. Instale e faça login com a sua conta GitHub
3. Clique em **"Add"** → **"Add Existing Repository"**
4. Selecione a pasta `/home/ubuntu/hugo_bot`
5. Clique em **"Publish repository"**
6. Escolha o nome: `volante-minho-bot`
7. **IMPORTANTE:** Desmarque "Keep this code private" (para ser público e grátis)
8. Clique em **"Publish repository"**

### Opção B: Via Comandos (Se preferir)

```bash
cd /home/ubuntu/hugo_bot

# Adicionar remote do GitHub (substitua SEU_USERNAME)
git remote add origin https://github.com/SEU_USERNAME/volante-minho-bot.git

# Fazer push
git branch -M main
git push -u origin main
```

Quando pedir credenciais:
- Username: seu username do GitHub
- Password: use um **Personal Access Token** (não a password normal)

---

## Passo 2: Fazer Deployment na Railway

### 2.1 Aceder à Railway

1. Abra o browser e vá a: **https://railway.app**
2. Faça login (se ainda não estiver)

### 2.2 Criar Novo Projeto

1. Clique no botão **"New Project"** (grande, no centro ou canto superior direito)
2. Selecione **"Deploy from GitHub repo"**
3. Se for a primeira vez:
   - Clique em **"Configure GitHub App"**
   - Autorize a Railway a aceder aos seus repositórios
   - Selecione **"All repositories"** ou apenas o `volante-minho-bot`
4. Selecione o repositório **volante-minho-bot** da lista

### 2.3 Aguardar Deploy

A Railway vai:
- Detetar que é Python ✅
- Instalar dependências ✅
- Iniciar o bot ✅

Isto demora 2-3 minutos. Vai ver uma barra de progresso.

---

## Passo 3: Configurar Volume (Base de Dados Persistente)

**MUITO IMPORTANTE:** Sem isto, a base de dados perde-se quando o bot reinicia!

### 3.1 Aceder às Configurações

1. No projeto, clique no **serviço do bot** (aparece como um cartão/card)
2. Vá ao separador **"Settings"** (no topo)

### 3.2 Criar Volume

1. Faça scroll até encontrar a secção **"Volumes"**
2. Clique no botão **"+ New Volume"** ou **"Add Volume"**
3. Preencha:
   - **Mount Path:** `/app/database`
   - **Size:** Deixe o padrão (1GB é mais que suficiente)
4. Clique em **"Add"** ou **"Create"**

### 3.3 Redeploy (Importante!)

Após adicionar o volume, o bot precisa de reiniciar:

1. Vá ao separador **"Deployments"**
2. Clique nos **três pontinhos (⋮)** no deployment mais recente
3. Selecione **"Redeploy"**
4. Aguarde 1-2 minutos

---

## Passo 4: Verificar se Está a Funcionar

### 4.1 Ver Logs

1. No serviço do bot, vá ao separador **"Deployments"**
2. Clique no deployment mais recente (o que está no topo)
3. Veja os logs em tempo real

**Deve ver algo como:**
```
🤖 Bot Volante Minho 2.0 V2 iniciado!
✅ Comandos configurados no menu do Telegram
Application started
```

### 4.2 Testar no Telegram

1. Abra o Telegram
2. Procure pelo bot: **@volante_minho_bot** (ou o nome que configurou)
3. Envie `/start`
4. O bot deve responder **imediatamente**

---

## Passo 5: Pronto! 🎉

O seu bot está agora:

✅ Ativo 24/7
✅ Com base de dados persistente
✅ Sem "cold start"
✅ Pronto para uso

---

## Resolução de Problemas Rápida

### Bot não responde no Telegram

**Verificar logs:**
1. Railway → Seu Projeto → Serviço → Deployments → Último deployment → Ver logs
2. Procure por erros em vermelho

**Erro comum: "No module named 'telegram'"**
- Solução: Verificar se `requirements.txt` está no repositório GitHub

### Base de dados perdeu-se

- **Causa:** Volume não foi configurado
- **Solução:** Seguir **Passo 3** novamente

### Bot está lento

- Verificar se não excedeu os créditos gratuitos
- Railway → Settings → Usage

---

## Custos

**Plano Gratuito:**
- $5 de crédito grátis por mês
- Este bot usa ~$1-2/mês
- **Totalmente suficiente!**

---

## Atualizações Futuras

Quando quiser atualizar o código:

1. Faça as alterações no código local
2. Faça commit e push para o GitHub:
   ```bash
   git add .
   git commit -m "Descrição da alteração"
   git push
   ```
3. A Railway faz **redeploy automático**!

---

## Precisa de Ajuda?

- Documentação Railway: https://docs.railway.app
- Suporte Railway: Muito responsivo via Discord

---

**Boa sorte com o deployment! 🚀**
