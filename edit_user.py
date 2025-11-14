from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import sqlite3
import logging

logger = logging.getLogger(__name__)

def get_db():
    """Conectar à base de dados"""
    conn = sqlite3.connect('database/hugo_bot.db')
    conn.row_factory = sqlite3.Row
    return conn

async def editar_user_command(update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /editar_user - Editar nome de utilizadores
    """
    user_id = update.effective_user.id
    
    # Verificar se é admin
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT is_admin FROM users WHERE telegram_id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user or not user['is_admin']:
        await update.message.reply_text("❌ Apenas administradores podem usar este comando.")
        conn.close()
        return
    
    # Listar todos os utilizadores
    cursor.execute('''
        SELECT telegram_id, shop_name, is_admin 
        FROM users 
        ORDER BY shop_name
    ''')
    
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        await update.message.reply_text("📋 Não há utilizadores registados.")
        return
    
    # Criar botões
    keyboard = []
    for user in users:
        admin_badge = " 👑" if user['is_admin'] else ""
        keyboard.append([
            InlineKeyboardButton(
                f"{user['shop_name']}{admin_badge} (ID: {user['telegram_id']})",
                callback_data=f"edit_user_{user['telegram_id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")])
    
    await update.message.reply_text(
        "👤 **Editar Utilizador**\n\n"
        "Selecione o utilizador que deseja editar:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_edit_user_callback(query, user_id_to_edit: int):
    """
    Processar seleção de utilizador para editar
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT shop_name FROM users WHERE telegram_id = ?', (user_id_to_edit,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        await query.edit_message_text("❌ Utilizador não encontrado.")
        return
    
    await query.edit_message_text(
        f"✏️ **Editar: {user['shop_name']}**\n\n"
        f"📝 Envie o novo nome para este utilizador:",
        parse_mode='Markdown'
    )
    
    # Guardar no context para processar a resposta
    query.from_user.id  # Admin ID
    return user_id_to_edit
