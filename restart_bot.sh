#!/bin/bash

# Parar todos os processos do bot
echo "A parar processos do bot..."
pkill -9 -f "python.*bot_v2.py" 2>/dev/null || true

# Aguardar
echo "A aguardar 5 segundos..."
sleep 5

# Limpar webhook
echo "A limpar webhook..."
curl -s "https://api.telegram.org/bot8365753572:AAGiZrUoYxxfYlrRWZaIwNGkKiWQ_EzdX78/deleteWebhook?drop_pending_updates=true" > /dev/null

# Aguardar mais
echo "A aguardar 10 segundos..."
sleep 10

# Iniciar bot
echo "A iniciar bot..."
cd /home/ubuntu/hugo_bot
source venv/bin/activate
nohup python bot_v2.py > bot_debug.log 2>&1 &

echo "Bot iniciado! PID: $!"
sleep 3

# Verificar se está a correr
if ps aux | grep -v grep | grep "python.*bot_v2.py" > /dev/null; then
    echo "✅ Bot a correr com sucesso!"
    tail -5 bot_debug.log
else
    echo "❌ Erro ao iniciar bot"
    tail -20 bot_debug.log
fi
