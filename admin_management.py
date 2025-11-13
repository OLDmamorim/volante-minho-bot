"""
Gestão de Administradores - Adicionar/Remover admins
"""
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Super admin (Hugo)
SUPER_ADMIN_ID = 228613920

def get_db():
    """Conectar à base de dados"""
    conn = sqlite3.connect('database/hugo_bot.db')
    conn.row_factory = sqlite3.Row
    return conn


async def adicionar_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /adicionar_admin - Elevar utilizador a admin (apenas super-admin)"""
    user_id = update.effective_user.id
    
    if user_id != SUPER_ADMIN_ID:
        await update.message.reply_text("❌ Apenas o super-administrador pode usar este comando.")
        return
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Buscar todos os utilizadores não-admin
    cursor.execute('''
        SELECT user_id, name, is_admin
        FROM users
        WHERE is_admin = 0
        ORDER BY name ASC
    ''')
    
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        await update.message.reply_text("ℹ️ Não há utilizadores para promover a admin.")
        return
    
    # Criar teclado com lista de utilizadores
    keyboard = []
    for user in users:
        keyboard.append([InlineKeyboardButton(
            f"👤 {user['name']}",
            callback_data=f"promote_admin_{user['user_id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")])
    
    await update.message.reply_text(
        "👑 **Adicionar Administrador**\n\n"
        "Selecione o utilizador que deseja promover a administrador:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def handle_promote_admin(query, user_id_to_promote: int):
    """Processar promoção de utilizador a admin"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Buscar nome do utilizador
    cursor.execute('SELECT name FROM users WHERE user_id = ?', (user_id_to_promote,))
    user = cursor.fetchone()
    
    if not user:
        await query.edit_message_text("❌ Utilizador não encontrado.")
        conn.close()
        return
    
    # Promover a admin
    cursor.execute('UPDATE users SET is_admin = 1 WHERE user_id = ?', (user_id_to_promote,))
    conn.commit()
    conn.close()
    
    logger.info(f"✅ Utilizador {user['name']} (ID: {user_id_to_promote}) promovido a admin")
    
    await query.edit_message_text(
        f"✅ **Utilizador Promovido!**\n\n"
        f"👤 **Nome:** {user['name']}\n"
        f"🆔 **ID:** `{user_id_to_promote}`\n\n"
        f"Este utilizador agora tem permissões de administrador.",
        parse_mode='Markdown'
    )
