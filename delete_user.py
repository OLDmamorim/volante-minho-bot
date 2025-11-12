# -*- coding: utf-8 -*-
"""
Comando para apagar utilizadores da base de dados
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import sqlite3
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

DB_PATH = "database/hugo_bot.db"
ADMIN_IDS = [789741735, 615966323, 228613920]


def get_db():
    """Conectar à base de dados"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


async def apagar_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /apagar_user - Apagar utilizador (admin)"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Você não tem permissão para usar este comando.")
        return
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Obter todos os utilizadores (exceto admins)
    cursor.execute('''
        SELECT telegram_id, username, shop_name, registered_at
        FROM users
        WHERE is_admin = FALSE
        ORDER BY shop_name ASC
    ''')
    
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        await update.message.reply_text("ℹ️ Não há utilizadores não-admin para apagar.")
        return
    
    keyboard = []
    for user in users:
        # Formatar data
        if user['registered_at']:
            try:
                date_obj = datetime.strptime(user['registered_at'], '%Y-%m-%d %H:%M:%S')
                date_str = date_obj.strftime('%d/%m/%Y')
            except:
                date_str = 'N/A'
        else:
            date_str = 'N/A'
        
        shop_name = user['shop_name'] or user['username'] or 'Sem nome'
        text = f"🗑️ {shop_name} (@{user['username'] or 'N/A'}) - {date_str}"
        
        keyboard.append([InlineKeyboardButton(
            text,
            callback_data=f"delete_user_{user['telegram_id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")])
    
    await update.message.reply_text(
        "🗑️ **Apagar Utilizador**\n\n"
        "⚠️ **ATENÇÃO:** Esta ação não pode ser desfeita!\n"
        "Selecione o utilizador que deseja apagar:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
