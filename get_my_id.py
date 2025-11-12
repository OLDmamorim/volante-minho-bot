# -*- coding: utf-8 -*-
"""
Script auxiliar para obter o ID do Telegram
Execute este script e envie uma mensagem ao bot para ver o seu ID
"""

import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

# Token do bot
BOT_TOKEN = '8365753572:AAGiZrUoYxxfYlrRWZaIwNGkKiWQ_EzdX78'

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def get_id(update: Update, context):
    """Mostra o ID do utilizador"""
    user = update.effective_user
    
    message = f"""
👤 **Informações do Utilizador:**

🆔 ID: `{user.id}`
👤 Nome: {user.first_name}
📝 Username: @{user.username if user.username else 'N/A'}

**Copie o ID acima e adicione-o à lista ADMIN_IDS no ficheiro config.py**
    """
    
    await update.message.reply_text(message, parse_mode='Markdown')
    
    print(f"\n{'='*50}")
    print(f"ID do utilizador: {user.id}")
    print(f"Nome: {user.first_name}")
    print(f"Username: @{user.username if user.username else 'N/A'}")
    print(f"{'='*50}\n")

def main():
    """Função principal"""
    print("\n" + "="*50)
    print("Script para obter ID do Telegram")
    print("="*50)
    print("\nInstruções:")
    print("1. Este script irá iniciar o bot temporariamente")
    print("2. Abra o Telegram e envie qualquer mensagem ao bot")
    print("3. O seu ID será mostrado aqui e no Telegram")
    print("4. Copie o ID e adicione-o ao ficheiro config.py")
    print("5. Pressione Ctrl+C para parar este script")
    print("="*50 + "\n")
    
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.ALL, get_id))
    
    print("✅ Bot iniciado! Aguardando mensagens...\n")
    application.run_polling()

if __name__ == '__main__':
    main()
