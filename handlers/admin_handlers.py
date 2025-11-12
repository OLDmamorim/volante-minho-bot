# -*- coding: utf-8 -*-
"""
Handlers para funcionalidades dos administradores
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import *
from database.db_manager import DatabaseManager
from utils.ics_generator import ICSGenerator
import os


async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra o menu principal do administrador"""
    keyboard = [
        [InlineKeyboardButton("🔔 Pedidos Pendentes", callback_data="admin_pending")],
        [InlineKeyboardButton("📊 Todos os Pedidos", callback_data="admin_all_requests")],
        [InlineKeyboardButton("ℹ️ Ajuda", callback_data="admin_help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(
            "🔧 **Menu Administrador**\n\nSelecione uma opção:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    elif update.callback_query:
        await update.callback_query.message.reply_text(
            "🔧 **Menu Administrador**\n\nSelecione uma opção:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


async def pending_requests_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db: DatabaseManager):
    """Handler para ver pedidos pendentes"""
    query = update.callback_query
    await query.answer()
    
    requests = db.get_pending_requests()
    
    if not requests:
        await query.edit_message_text(MESSAGES['no_pending_requests'])
        await show_admin_menu(update, context)
        return ADMIN_MENU
    
    # Mostrar lista de pedidos pendentes
    text = "🔔 **Pedidos Pendentes:**\n\n"
    
    keyboard = []
    
    for req in requests[:10]:  # Mostrar apenas os 10 mais recentes
        text += f"📋 **#{req['id']}** - {req['shop_name']}\n"
        text += f"   Tipo: {req['request_type']}\n"
        text += f"   Data: {req['start_date']} ({req['period']})\n\n"
        
        keyboard.append([
            InlineKeyboardButton(
                f"#{req['id']} - {req['shop_name']}",
                callback_data=f"view_{req['id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="admin_back")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return ADMIN_MENU


async def view_request_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db: DatabaseManager):
    """Handler para ver detalhes de um pedido"""
    query = update.callback_query
    await query.answer()
    
    # Extrair ID do pedido
    request_id = int(query.data.replace("view_", ""))
    
    # Obter pedido
    request = db.get_request(request_id)
    
    if not request:
        await query.edit_message_text("❌ Pedido não encontrado.")
        await show_admin_menu(update, context)
        return ADMIN_MENU
    
    # Formatar detalhes
    text = f"📋 **Detalhes do Pedido #{request['id']}**\n\n"
    text += f"🏪 Loja: {request['shop_name']}\n"
    text += f"📝 Tipo: {request['request_type']}\n"
    text += f"📅 Data: {request['start_date']}\n"
    text += f"🕐 Período: {request['period']}\n"
    text += f"📊 Status: {request['status']}\n"
    text += f"🕒 Criado em: {request['created_at']}\n"
    
    if request['status'] == 'Rejeitado' and request['rejection_reason']:
        text += f"\n❌ Motivo da rejeição: {request['rejection_reason']}\n"
    
    # Botões de ação
    keyboard = []
    
    if request['status'] == 'Pendente':
        keyboard.append([
            InlineKeyboardButton("✅ Aprovar", callback_data=f"approve_{request_id}"),
            InlineKeyboardButton("❌ Rejeitar", callback_data=f"reject_{request_id}")
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="admin_pending")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return VIEWING_REQUEST


async def approve_request_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db: DatabaseManager):
    """Handler para aprovar pedido"""
    query = update.callback_query
    await query.answer()
    
    # Extrair ID do pedido
    request_id = int(query.data.replace("approve_", ""))
    admin_id = update.effective_user.id
    
    # Obter pedido
    request = db.get_request(request_id)
    
    if not request:
        await query.edit_message_text("❌ Pedido não encontrado.")
        return ADMIN_MENU
    
    # Aprovar pedido
    if db.approve_request(request_id, admin_id):
        await query.edit_message_text("✅ Pedido aprovado com sucesso!")
        
        # Notificar loja
        try:
            await context.bot.send_message(
                chat_id=request['shop_telegram_id'],
                text=MESSAGES['request_approved']
            )
        except Exception as e:
            print(f"Erro ao notificar loja: {e}")
        
        # Gerar ficheiro .ics
        try:
            filename = f"/tmp/pedido_{request_id}.ics"
            ICSGenerator.save_event_to_file(
                request['shop_name'],
                request['request_type'],
                request['start_date'],
                request['period'],
                filename
            )
            
            # Enviar ficheiro ao admin
            with open(filename, 'rb') as f:
                await context.bot.send_document(
                    chat_id=admin_id,
                    document=f,
                    filename=f"pedido_{request_id}.ics",
                    caption="📅 Adicione este evento ao seu calendário"
                )
            
            # Gerar link do Google Calendar
            google_link = ICSGenerator.create_google_calendar_link(
                request['shop_name'],
                request['request_type'],
                request['start_date'],
                request['period']
            )
            
            keyboard = [
                [InlineKeyboardButton("📅 Adicionar ao Google Calendar", url=google_link)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await context.bot.send_message(
                chat_id=admin_id,
                text="Ou clique no botão abaixo para adicionar diretamente ao Google Calendar:",
                reply_markup=reply_markup
            )
            
            # Remover ficheiro temporário
            os.remove(filename)
            
        except Exception as e:
            print(f"Erro ao gerar calendário: {e}")
            await context.bot.send_message(
                chat_id=admin_id,
                text="⚠️ Erro ao gerar ficheiro de calendário."
            )
        
        await show_admin_menu(update, context)
        return ADMIN_MENU
    else:
        await query.edit_message_text("❌ Erro ao aprovar pedido.")
        return ADMIN_MENU


async def reject_request_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para iniciar rejeição de pedido"""
    query = update.callback_query
    await query.answer()
    
    # Extrair ID do pedido
    request_id = int(query.data.replace("reject_", ""))
    
    # Guardar no contexto
    context.user_data['rejecting_request_id'] = request_id
    
    await query.edit_message_text(MESSAGES['enter_rejection_reason'])
    
    return ENTERING_REJECTION_REASON


async def receive_rejection_reason(update: Update, context: ContextTypes.DEFAULT_TYPE, db: DatabaseManager):
    """Handler para receber motivo de rejeição"""
    reason = update.message.text.strip()
    request_id = context.user_data.get('rejecting_request_id')
    admin_id = update.effective_user.id
    
    if not request_id:
        await update.message.reply_text("❌ Erro: Pedido não encontrado.")
        await show_admin_menu(update, context)
        return ADMIN_MENU
    
    # Obter pedido
    request = db.get_request(request_id)
    
    if not request:
        await update.message.reply_text("❌ Pedido não encontrado.")
        context.user_data.clear()
        await show_admin_menu(update, context)
        return ADMIN_MENU
    
    # Rejeitar pedido
    if db.reject_request(request_id, admin_id, reason):
        await update.message.reply_text("✅ Pedido rejeitado com sucesso!")
        
        # Notificar loja
        try:
            await context.bot.send_message(
                chat_id=request['shop_telegram_id'],
                text=MESSAGES['request_rejected'].format(reason=reason)
            )
        except Exception as e:
            print(f"Erro ao notificar loja: {e}")
        
        context.user_data.clear()
        await show_admin_menu(update, context)
        return ADMIN_MENU
    else:
        await update.message.reply_text("❌ Erro ao rejeitar pedido.")
        context.user_data.clear()
        await show_admin_menu(update, context)
        return ADMIN_MENU


async def all_requests_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db: DatabaseManager):
    """Handler para ver todos os pedidos"""
    query = update.callback_query
    await query.answer()
    
    # Obter estatísticas
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total FROM requests")
    total = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM requests WHERE status = 'Pendente'")
    pending = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM requests WHERE status = 'Aprovado'")
    approved = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM requests WHERE status = 'Rejeitado'")
    rejected = cursor.fetchone()['total']
    
    conn.close()
    
    text = "📊 **Estatísticas de Pedidos:**\n\n"
    text += f"📋 Total: {total}\n"
    text += f"🟡 Pendentes: {pending}\n"
    text += f"✅ Aprovados: {approved}\n"
    text += f"❌ Rejeitados: {rejected}\n"
    
    keyboard = [
        [InlineKeyboardButton("🔙 Voltar", callback_data="admin_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return ADMIN_MENU


async def admin_back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para voltar ao menu admin"""
    query = update.callback_query
    await query.answer()
    
    await query.delete_message()
    await show_admin_menu(update, context)
    return ADMIN_MENU
