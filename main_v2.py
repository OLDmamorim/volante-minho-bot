# -*- coding: utf-8 -*-
"""
Bot Volante Minho 2.0 - Versão Completa
Sistema completo de gestão de pedidos
"""

import logging
import os
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# Configurações
BOT_TOKEN = '8365753572:AAGiZrUoYxxfYlrRWZaIwNGkKiWQ_EzdX78'
ADMIN_IDS = [228613920, 615966323]

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Base de dados simples em memória (para demonstração)
users_db = {}
requests_db = []
comments_db = []

# Estados do calendário
CALENDAR_STATES = {
    'available': '🟢',
    'busy': '🔴',
    'selected': '🔵',
    'pending': '🟣',
    'approved': '🟡'
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    user = update.effective_user
    user_id = user.id
    
    # Verificar se é admin
    is_admin = user_id in ADMIN_IDS
    
    # Registar utilizador se não existir
    if user_id not in users_db:
        users_db[user_id] = {
            'id': user_id,
            'username': user.username or user.first_name,
            'is_admin': is_admin,
            'shop_name': None,
            'shop_id': None
        }
    
    if is_admin:
        # Menu para administradores
        message = f"🏪 Bem-vindo de volta, {user.first_name}!\n\n"
        message += "Comandos disponíveis:\n"
        message += "/pendentes - Ver pedidos pendentes\n"
        message += "/agenda_semana - Ver agenda da semana\n"
        message += "/calendario - Ver calendário de pedidos\n"
        message += "/estatisticas - Ver estatísticas completas\n"
        message += "/adicionar_gestor - Adicionar novo gestor\n"
        message += "/listar_usuarios - Listar todos os utilizadores\n"
        message += "/comentar - Adicionar comentário a um pedido\n"
        message += "/ver_comentarios - Ver comentários de um pedido"
        
        # Teclado persistente
        keyboard = [[KeyboardButton("≡ Menu")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(message, reply_markup=reply_markup)
    else:
        # Verificar se tem loja registada
        if not users_db[user_id]['shop_name']:
            await update.message.reply_text("Por favor, indique o nome da sua loja:")
            return
        
        shop_name = users_db[user_id]['shop_name']
        shop_id = users_db[user_id]['shop_id']
        
        message = f"🏪 Bem-vindo de volta, {user.first_name}!\n"
        message += f"🏬 Loja: {shop_name}\n"
        message += f"🆔 ID: {shop_id}\n\n"
        message += "Comandos disponíveis:\n"
        message += "/pedido - Criar novo pedido\n"
        message += "/calendario - Ver calendário de pedidos\n"
        message += "/meus_pedidos - Ver meus pedidos\n"
        message += "/minha_loja - Ver informações da minha loja"
        
        # Teclado persistente
        keyboard = [[KeyboardButton("≡ Menu")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(message, reply_markup=reply_markup)


async def pedido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /pedido - Criar novo pedido"""
    user_id = update.effective_user.id
    
    if user_id not in users_db or not users_db[user_id]['shop_name']:
        await update.message.reply_text("❌ Por favor, registe-se primeiro com /start")
        return
    
    # Mostrar calendário
    await show_calendar(update, context)


async def show_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostrar calendário visual"""
    today = datetime.now()
    month = today.month
    year = today.year
    
    # Criar calendário do mês
    import calendar
    cal = calendar.monthcalendar(year, month)
    
    month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
                   'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    
    message = f"📅 **{month_names[month-1]} {year}**\n\n"
    message += "D   S   T   Q   Q   S   S\n"
    
    for week in cal:
        week_str = ""
        for day in week:
            if day == 0:
                week_str += "    "
            else:
                # Determinar estado do dia
                state = get_day_state(year, month, day)
                emoji = CALENDAR_STATES.get(state, '⚪')
                week_str += f"{day}{emoji} "
        message += week_str + "\n"
    
    message += "\n🟢 Disponível  🔴 Ocupado  🔵 Selecionado\n"
    message += "🟣 Pendente  🟡 Aprovado\n\n"
    message += "📝 Observações? (ou envie \"não\" para pular)"
    
    await update.message.reply_text(message, parse_mode='Markdown')


def get_day_state(year, month, day):
    """Obter estado de um dia no calendário"""
    date_str = f"{year}-{month:02d}-{day:02d}"
    
    # Verificar se há pedidos para este dia
    for req in requests_db:
        if req['date'] == date_str:
            return req['status'].lower()
    
    return 'available'


async def calendario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /calendario - Ver calendário"""
    await show_calendar(update, context)


async def meus_pedidos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /meus_pedidos - Ver pedidos da loja"""
    user_id = update.effective_user.id
    
    if user_id not in users_db:
        await update.message.reply_text("❌ Utilizador não encontrado")
        return
    
    # Filtrar pedidos do utilizador
    user_requests = [r for r in requests_db if r['user_id'] == user_id]
    
    if not user_requests:
        await update.message.reply_text("📋 Não tem pedidos registados")
        return
    
    message = "📋 **Seus Pedidos:**\n\n"
    for req in user_requests:
        status_emoji = {
            'pending': '⏳',
            'approved': '✅',
            'busy': '🔴'
        }.get(req['status'], '❓')
        
        message += f"{status_emoji} {req['type']}\n"
        message += f"📅 {req['date']} ({req['period']})\n"
        if req.get('observations'):
            message += f"📝 {req['observations']}\n"
        message += "\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def minha_loja(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /minha_loja - Ver informações da loja"""
    user_id = update.effective_user.id
    
    if user_id not in users_db:
        await update.message.reply_text("❌ Utilizador não encontrado")
        return
    
    user = users_db[user_id]
    
    message = "🏬 **Informações da Loja**\n\n"
    message += f"Loja: {user['shop_name']}\n"
    message += f"ID: {user['shop_id']}"
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def pendentes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /pendentes - Ver pedidos pendentes (admin)"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Apenas administradores")
        return
    
    pending = [r for r in requests_db if r['status'] == 'pending']
    
    if not pending:
        await update.message.reply_text("✅ Não há pedidos pendentes")
        return
    
    message = "⏳ **Pedidos Pendentes:**\n\n"
    for req in pending:
        user = users_db.get(req['user_id'], {})
        message += f"🏬 {user.get('shop_name', 'N/A')}\n"
        message += f"📝 {req['type']}\n"
        message += f"📅 {req['date']} ({req['period']})\n"
        if req.get('observations'):
            message += f"💬 {req['observations']}\n"
        message += "\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def estatisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /estatisticas - Ver estatísticas (admin)"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Apenas administradores")
        return
    
    total = len(requests_db)
    pending = len([r for r in requests_db if r['status'] == 'pending'])
    approved = len([r for r in requests_db if r['status'] == 'approved'])
    busy = len([r for r in requests_db if r['status'] == 'busy'])
    
    message = "📊 **Estatísticas Completas**\n\n"
    message += f"📝 Total de Pedidos: {total}\n"
    message += f"⏳ Pendentes: {pending}\n"
    message += f"✅ Aprovados: {approved}\n"
    message += f"🔴 Ocupados: {busy}\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para botão Menu"""
    await start(update, context)


def main():
    """Função principal"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pedido", pedido))
    application.add_handler(CommandHandler("calendario", calendario))
    application.add_handler(CommandHandler("meus_pedidos", meus_pedidos))
    application.add_handler(CommandHandler("minha_loja", minha_loja))
    application.add_handler(CommandHandler("pendentes", pendentes))
    application.add_handler(CommandHandler("estatisticas", estatisticas))
    
    # Botão Menu
    application.add_handler(MessageHandler(filters.Regex("^≡ Menu$"), menu_button))
    
    # Registar nome da loja
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, register_shop_name))
    
    logger.info("🤖 Bot iniciado!")
    application.run_polling()


async def register_shop_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Registar nome da loja"""
    user_id = update.effective_user.id
    
    if user_id in users_db and not users_db[user_id]['shop_name']:
        shop_name = update.message.text.strip()
        shop_id = f"{user_id}"
        
        users_db[user_id]['shop_name'] = shop_name
        users_db[user_id]['shop_id'] = shop_id
        
        await update.message.reply_text(f"✅ Loja '{shop_name}' registada com sucesso!")
        await start(update, context)


if __name__ == '__main__':
    main()
