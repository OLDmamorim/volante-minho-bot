#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Volante Minho 2.0 - Bot do Telegram
Versão completa com todos os comandos
"""
import logging
import sqlite3
from datetime import datetime, timedelta
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

# Configuração
BOT_TOKEN = "8365753572:AAGiZrUoYxxfYlrRWZaIwNGkKiWQ_EzdX78"
ADMIN_IDS = [228613920, 615966323]
DB_PATH = "database/hugo_bot.db"

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_db():
    """Retorna conexão à base de dados"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    user = update.effective_user
    user_id = user.id
    is_admin = user_id in ADMIN_IDS
    
    # Registar utilizador
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (user_id,))
    existing_user = cursor.fetchone()
    
    if not existing_user:
        cursor.execute('''
            INSERT INTO users (telegram_id, username, is_admin, shop_name)
            VALUES (?, ?, ?, ?)
        ''', (user_id, user.username or user.first_name, is_admin, None))
        conn.commit()
    
    conn.close()
    
    if is_admin:
        welcome_text = f"""
👋 Bem-vindo de volta, {user.first_name}!

**Comandos disponíveis:**

/pendentes - Ver pedidos pendentes
/agenda_semana - Ver agenda da semana
/calendario - Ver calendário de pedidos
/estatisticas - Ver estatísticas completas
/adicionar_gestor - Adicionar novo gestor
/listar_usuarios - Listar todos os utilizadores
/comentar - Adicionar comentário a um pedido
/ver_comentarios - Ver comentários de um pedido
/help - Mostrar ajuda
"""
    else:
        # Verificar se tem loja registada
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT shop_name FROM users WHERE telegram_id = ?', (user_id,))
        user_data = cursor.fetchone()
        conn.close()
        
        if not user_data or not user_data['shop_name']:
            await update.message.reply_text("Por favor, indique o nome da sua loja:")
            return
        
        shop_name = user_data['shop_name']
        
        welcome_text = f"""
👋 Bem-vindo de volta, {user.first_name}!
🏬 Loja: {shop_name}
🆔 ID: {user_id}

**Comandos disponíveis:**

/pedido - Criar novo pedido
/calendario - Ver calendário de pedidos
/meus_pedidos - Ver meus pedidos
/minha_loja - Ver informações da minha loja
/help - Mostrar ajuda
"""
    
    # Botão Menu persistente
    keyboard = [[KeyboardButton("≡ Menu")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)


async def pedido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /pedido - Criar novo pedido"""
    user_id = update.effective_user.id
    
    # Verificar se tem loja
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT shop_name FROM users WHERE telegram_id = ?', (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    
    if not user_data or not user_data['shop_name']:
        await update.message.reply_text("❌ Por favor, registe-se primeiro com /start")
        return
    
    # Mostrar tipos de pedido
    keyboard = [
        [InlineKeyboardButton("🔧 Apoio", callback_data="tipo_apoio")],
        [InlineKeyboardButton("🏖️ Férias", callback_data="tipo_ferias")],
        [InlineKeyboardButton("📋 Outros", callback_data="tipo_outros")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📝 **Novo Pedido**\n\nSelecione o tipo de pedido:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def meus_pedidos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /meus_pedidos"""
    user_id = update.effective_user.id
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM requests 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (user_id,))
    requests = cursor.fetchall()
    conn.close()
    
    if not requests:
        await update.message.reply_text("📋 Não tem pedidos registados.")
        return
    
    message = "📋 **Seus Pedidos:**\n\n"
    
    for req in requests:
        status_emoji = {
            'Pendente': '⏳',
            'Aprovado': '✅',
            'Rejeitado': '❌'
        }.get(req['status'], '❓')
        
        message += f"{status_emoji} **{req['request_type']}**\n"
        message += f"📅 {req['date']} ({req['period']})\n"
        
        if req['observations']:
            message += f"📝 {req['observations']}\n"
        
        message += "\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def minha_loja(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /minha_loja"""
    user_id = update.effective_user.id
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    
    if not user_data:
        await update.message.reply_text("❌ Utilizador não encontrado.")
        return
    
    message = f"""
🏬 **Informações da Loja**

Loja: {user_data['shop_name'] or 'N/A'}
ID: {user_data['telegram_id']}
"""
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def pendentes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /pendentes"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Apenas administradores podem usar este comando.")
        return
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.*, u.shop_name 
        FROM requests r
        JOIN users u ON r.user_id = u.telegram_id
        WHERE r.status = 'Pendente'
        ORDER BY r.created_at DESC
    ''')
    requests = cursor.fetchall()
    conn.close()
    
    if not requests:
        await update.message.reply_text("✅ Não há pedidos pendentes!")
        return
    
    message = f"⏳ **Pedidos Pendentes ({len(requests)})**\n\n"
    
    for req in requests:
        message += f"""
🏬 {req['shop_name']}
📝 {req['request_type']}
📅 {req['date']} ({req['period']})
"""
        if req['observations']:
            message += f"💬 {req['observations']}\n"
        message += "---\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def estatisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /estatisticas"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Apenas administradores podem usar este comando.")
        return
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Total
    cursor.execute('SELECT COUNT(*) as total FROM requests')
    total = cursor.fetchone()['total']
    
    # Por status
    cursor.execute('SELECT status, COUNT(*) as count FROM requests GROUP BY status')
    por_status = cursor.fetchall()
    
    conn.close()
    
    pendentes = sum(r['count'] for r in por_status if r['status'] == 'Pendente')
    aprovados = sum(r['count'] for r in por_status if r['status'] == 'Aprovado')
    rejeitados = sum(r['count'] for r in por_status if r['status'] == 'Rejeitado')
    
    message = f"""
📊 **Estatísticas Completas**

📋 Total de Pedidos: {total}

**Por Status:**
⏳ Pendentes: {pendentes}
✅ Aprovados: {aprovados}
❌ Rejeitados: {rejeitados}
"""
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def calendario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /calendario"""
    message = """
📆 **Calendário de Pedidos**

Use /pedido para criar um novo pedido e selecionar a data no calendário interativo.
"""
    await update.message.reply_text(message, parse_mode='Markdown')


async def agenda_semana(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /agenda_semana"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Apenas administradores podem usar este comando.")
        return
    
    await update.message.reply_text("📅 **Agenda da Semana**\n\nFuncionalidade em desenvolvimento.")


async def adicionar_gestor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /adicionar_gestor"""
    await update.message.reply_text("🚧 Funcionalidade em desenvolvimento!")


async def listar_usuarios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /listar_usuarios"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Apenas administradores podem usar este comando.")
        return
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users ORDER BY registered_at DESC')
    users = cursor.fetchall()
    conn.close()
    
    message = f"👥 **Utilizadores ({len(users)})**\n\n"
    
    for u in users[:20]:
        emoji = "👑" if u['is_admin'] else "🏪"
        message += f"{emoji} {u['username']} - {u['shop_name'] or 'Sem loja'}\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def comentar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /comentar"""
    await update.message.reply_text("🚧 Funcionalidade em desenvolvimento!")


async def ver_comentarios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /ver_comentarios"""
    await update.message.reply_text("🚧 Funcionalidade em desenvolvimento!")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help"""
    await start(update, context)


async def menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para botão Menu"""
    await start(update, context)


async def register_shop_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Registar nome da loja"""
    user_id = update.effective_user.id
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT shop_name FROM users WHERE telegram_id = ?', (user_id,))
    user_data = cursor.fetchone()
    
    if user_data and not user_data['shop_name']:
        shop_name = update.message.text.strip()
        cursor.execute('UPDATE users SET shop_name = ? WHERE telegram_id = ?', (shop_name, user_id))
        conn.commit()
        conn.close()
        
        await update.message.reply_text(f"✅ Loja '{shop_name}' registada com sucesso!")
        await start(update, context)
    else:
        conn.close()


async def setup_commands(application: Application):
    """Configurar comandos do bot"""
    # Comandos para lojas
    commands = [
        BotCommand("start", "Iniciar o bot"),
        BotCommand("pedido", "Criar novo pedido"),
        BotCommand("calendario", "Ver calendário de pedidos"),
        BotCommand("meus_pedidos", "Ver meus pedidos"),
        BotCommand("minha_loja", "Ver informações da minha loja"),
        BotCommand("pendentes", "Ver pedidos pendentes"),
        BotCommand("agenda_semana", "Ver agenda da semana"),
        BotCommand("estatisticas", "Ver estatísticas completas"),
        BotCommand("adicionar_gestor", "Adicionar novo gestor"),
        BotCommand("listar_usuarios", "Listar todos os utilizadores"),
        BotCommand("comentar", "Adicionar comentário a um pedido"),
        BotCommand("ver_comentarios", "Ver comentários de um pedido"),
        BotCommand("help", "Mostrar ajuda")
    ]
    
    await application.bot.set_my_commands(commands)
    logger.info("✅ Comandos configurados no menu do Telegram")


def main():
    """Função principal"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pedido", pedido))
    application.add_handler(CommandHandler("meus_pedidos", meus_pedidos))
    application.add_handler(CommandHandler("minha_loja", minha_loja))
    application.add_handler(CommandHandler("pendentes", pendentes))
    application.add_handler(CommandHandler("estatisticas", estatisticas))
    application.add_handler(CommandHandler("calendario", calendario))
    application.add_handler(CommandHandler("agenda_semana", agenda_semana))
    application.add_handler(CommandHandler("agendasemana", agenda_semana))
    application.add_handler(CommandHandler("adicionar_gestor", adicionar_gestor))
    application.add_handler(CommandHandler("adicionargestor", adicionar_gestor))
    application.add_handler(CommandHandler("listar_usuarios", listar_usuarios))
    application.add_handler(CommandHandler("listarusuarios", listar_usuarios))
    application.add_handler(CommandHandler("comentar", comentar))
    application.add_handler(CommandHandler("ver_comentarios", ver_comentarios))
    application.add_handler(CommandHandler("vercomentarios", ver_comentarios))
    application.add_handler(CommandHandler("help", help_command))
    
    # Botão Menu
    application.add_handler(MessageHandler(filters.Regex("^≡ Menu$"), menu_button))
    
    # Registar nome da loja
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, register_shop_name))
    
    # Configurar comandos
    application.post_init = setup_commands
    
    logger.info("🤖 Bot Volante Minho 2.0 iniciado!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
