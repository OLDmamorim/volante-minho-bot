# -*- coding: utf-8 -*-
"""
Comandos adicionais para lojas
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.calendar_utils import TelegramCalendar


async def pedido_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """Comando /pedido - Criar novo pedido"""
    user_id = update.effective_user.id
    
    # Verificar se utilizador existe
    user = db.get_user_by_telegram_id(user_id)
    if not user or not user['shop_name']:
        await update.message.reply_text("❌ Por favor, registe-se primeiro com /start")
        return
    
    # Mostrar opções de tipo de pedido
    keyboard = [
        [InlineKeyboardButton("🔧 Apoio", callback_data="request_type_apoio")],
        [InlineKeyboardButton("🏖️ Férias", callback_data="request_type_ferias")],
        [InlineKeyboardButton("📋 Outros", callback_data="request_type_outros")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📝 **Novo Pedido**\n\nSelecione o tipo de pedido:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    # Guardar estado
    context.user_data['creating_request'] = True
    context.user_data['request_data'] = {}


async def calendario_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """Comando /calendario - Ver calendário"""
    calendar = TelegramCalendar()
    await update.message.reply_text(
        "📅 **Calendário de Pedidos**\n\nSelecione uma data:",
        reply_markup=calendar.create_calendar(),
        parse_mode='Markdown'
    )


async def meus_pedidos_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """Comando /meus_pedidos - Ver pedidos da loja"""
    user_id = update.effective_user.id
    
    # Obter pedidos do utilizador
    requests = db.get_requests_by_user(user_id)
    
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
        
        if req.get('observations'):
            message += f"📝 {req['observations']}\n"
        
        if req['status'] == 'Rejeitado' and req.get('rejection_reason'):
            message += f"❌ Motivo: {req['rejection_reason']}\n"
        
        message += "\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def minha_loja_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """Comando /minha_loja - Ver informações da loja"""
    user_id = update.effective_user.id
    
    user = db.get_user_by_telegram_id(user_id)
    
    if not user:
        await update.message.reply_text("❌ Utilizador não encontrado.")
        return
    
    message = "🏬 **Informações da Loja**\n\n"
    message += f"Loja: {user['shop_name']}\n"
    message += f"ID: {user['telegram_id']}"
    
    await update.message.reply_text(message, parse_mode='Markdown')
