# -*- coding: utf-8 -*-
"""
Handlers para funcionalidades das lojas
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import *
from database.db_manager import DatabaseManager
from utils.calendar_utils import TelegramCalendar

# Import show_admin_menu from admin_handlers
from handlers import admin_handlers


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: DatabaseManager):
    """Handler para o comando /start"""
    user = update.effective_user
    telegram_id = user.id
    username = user.username or user.first_name
    
    # Verificar se é admin
    is_admin = telegram_id in ADMIN_IDS
    
    # Verificar se utilizador existe
    db_user = db.get_user(telegram_id)
    
    if db_user is None:
        # Criar utilizador
        db.create_user(telegram_id, username, is_admin=is_admin)
        
        if is_admin:
            # Admin não precisa de nome de loja
            await update.message.reply_text(MESSAGES['welcome_admin'])
            await admin_handlers.show_admin_menu(update, context)
            return ADMIN_MENU
        else:
            # Solicitar nome da loja
            await update.message.reply_text(MESSAGES['welcome_new'])
            return AWAITING_SHOP_NAME
    else:
        # Utilizador já existe
        if is_admin or db_user['is_admin']:
            await update.message.reply_text(MESSAGES['welcome_admin'])
            await admin_handlers.show_admin_menu(update, context)
            return ADMIN_MENU
        else:
            shop_name = db_user['shop_name']
            await update.message.reply_text(
                MESSAGES['welcome_back'].format(shop_name=shop_name)
            )
            await show_shop_menu(update, context)
            return MAIN_MENU


async def receive_shop_name(update: Update, context: ContextTypes.DEFAULT_TYPE, db: DatabaseManager):
    """Handler para receber o nome da loja"""
    shop_name = update.message.text.strip()
    telegram_id = update.effective_user.id
    
    # Atualizar nome da loja
    db.update_shop_name(telegram_id, shop_name)
    
    await update.message.reply_text(
        MESSAGES['shop_registered'].format(shop_name=shop_name)
    )
    
    await show_shop_menu(update, context)
    return MAIN_MENU


async def show_shop_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra o menu principal da loja"""
    keyboard = [
        [InlineKeyboardButton("📝 Novo Pedido", callback_data="shop_new_request")],
        [InlineKeyboardButton("📋 Meus Pedidos", callback_data="shop_my_requests")],
        [InlineKeyboardButton("ℹ️ Ajuda", callback_data="shop_help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(
            "Selecione uma opção:",
            reply_markup=reply_markup
        )
    else:
        await update.callback_query.message.reply_text(
            "Selecione uma opção:",
            reply_markup=reply_markup
        )


async def new_request_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para iniciar novo pedido"""
    query = update.callback_query
    await query.answer()
    
    # Mostrar tipos de pedido
    keyboard = [
        [InlineKeyboardButton(req_type, callback_data=f"request_type_{req_type}")]
        for req_type in REQUEST_TYPES
    ]
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        MESSAGES['select_request_type'],
        reply_markup=reply_markup
    )
    
    return SELECTING_REQUEST_TYPE


async def select_request_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para seleção do tipo de pedido"""
    query = update.callback_query
    await query.answer()
    
    # Extrair tipo de pedido
    request_type = query.data.replace("request_type_", "")
    
    # Guardar no contexto
    context.user_data['request_type'] = request_type
    
    # Mostrar calendário
    cal = TelegramCalendar()
    await query.edit_message_text(
        MESSAGES['select_date'],
        reply_markup=cal.create_calendar()
    )
    
    return SELECTING_DATE


async def select_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para seleção de data"""
    query = update.callback_query
    await query.answer()
    
    # Processar seleção
    result = TelegramCalendar.process_selection(query.data)
    
    if result[0] == 'day':
        # Data selecionada
        _, year, month, day = result
        date_str = TelegramCalendar.format_date(year, month, day)
        date_display = TelegramCalendar.format_date_pt(year, month, day)
        
        # Guardar no contexto
        context.user_data['date'] = date_str
        context.user_data['date_display'] = date_display
        
        # Mostrar períodos
        keyboard = [
            [InlineKeyboardButton(period, callback_data=f"period_{period}")]
            for period in CALENDAR_PERIODS.keys()
        ]
        keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            MESSAGES['select_period'],
            reply_markup=reply_markup
        )
        
        return SELECTING_PERIOD
        
    elif result[0] in ['prev', 'next']:
        # Navegação entre meses
        _, year, month = result
        cal = TelegramCalendar(year, month)
        
        await query.edit_message_text(
            MESSAGES['select_date'],
            reply_markup=cal.create_calendar()
        )
        
        return SELECTING_DATE
        
    elif result[0] == 'cancel':
        await query.edit_message_text("❌ Operação cancelada.")
        await show_shop_menu(update, context)
        return MAIN_MENU
    
    # Ignorar outros cliques
    return SELECTING_DATE


async def select_period(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para seleção de período"""
    query = update.callback_query
    await query.answer()
    
    # Extrair período
    period = query.data.replace("period_", "")
    
    # Guardar no contexto
    context.user_data['period'] = period
    
    # Mostrar confirmação
    request_type = context.user_data.get('request_type')
    date_display = context.user_data.get('date_display')
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirmar", callback_data="confirm_request")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        MESSAGES['confirm_request'].format(
            request_type=request_type,
            date=date_display,
            period=period
        ),
        reply_markup=reply_markup
    )
    
    return CONFIRMING_REQUEST


async def confirm_request(update: Update, context: ContextTypes.DEFAULT_TYPE, db: DatabaseManager):
    """Handler para confirmar pedido"""
    query = update.callback_query
    await query.answer()
    
    telegram_id = update.effective_user.id
    request_type = context.user_data.get('request_type')
    date = context.user_data.get('date')
    period = context.user_data.get('period')
    
    # Criar pedido na base de dados
    request_id = db.create_request(telegram_id, request_type, date, period)
    
    if request_id:
        await query.edit_message_text(MESSAGES['request_created'])
        
        # Notificar admins
        user = db.get_user(telegram_id)
        shop_name = user['shop_name']
        date_display = context.user_data.get('date_display')
        
        notification_text = MESSAGES['new_request_notification'].format(
            shop_name=shop_name,
            request_type=request_type,
            date=date_display,
            period=period
        )
        
        # Enviar notificação para cada admin
        for admin_id in ADMIN_IDS:
            try:
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Aprovar", callback_data=f"approve_{request_id}"),
                        InlineKeyboardButton("❌ Rejeitar", callback_data=f"reject_{request_id}")
                    ],
                    [InlineKeyboardButton("👁️ Ver Detalhes", callback_data=f"view_{request_id}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=notification_text,
                    reply_markup=reply_markup
                )
                
                db.create_notification(admin_id, notification_text, request_id)
            except Exception as e:
                print(f"Erro ao notificar admin {admin_id}: {e}")
        
        # Limpar contexto
        context.user_data.clear()
        
        await show_shop_menu(update, context)
        return MAIN_MENU
    else:
        await query.edit_message_text("❌ Erro ao criar pedido. Tente novamente.")
        await show_shop_menu(update, context)
        return MAIN_MENU


async def my_requests_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db: DatabaseManager):
    """Handler para ver pedidos da loja"""
    query = update.callback_query
    await query.answer()
    
    telegram_id = update.effective_user.id
    requests = db.get_shop_requests(telegram_id)
    
    if not requests:
        await query.edit_message_text("ℹ️ Você ainda não tem pedidos.")
        await show_shop_menu(update, context)
        return MAIN_MENU
    
    # Formatar lista de pedidos
    text = "📋 **Seus Pedidos:**\n\n"
    
    for req in requests[:10]:  # Mostrar apenas os 10 mais recentes
        status_emoji = {
            'Pendente': '🟡',
            'Aprovado': '✅',
            'Rejeitado': '❌'
        }.get(req['status'], '⚪')
        
        text += f"{status_emoji} **{req['request_type']}** - {req['start_date']} ({req['period']})\n"
        text += f"   Status: {req['status']}\n"
        
        if req['status'] == 'Rejeitado' and req['rejection_reason']:
            text += f"   Motivo: {req['rejection_reason']}\n"
        
        text += "\n"
    
    await query.edit_message_text(text, parse_mode='Markdown')
    await show_shop_menu(update, context)
    return MAIN_MENU


async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para cancelar operação"""
    query = update.callback_query
    await query.answer()
    
    context.user_data.clear()
    
    await query.edit_message_text(MESSAGES['request_cancelled'])
    await show_shop_menu(update, context)
    return MAIN_MENU
