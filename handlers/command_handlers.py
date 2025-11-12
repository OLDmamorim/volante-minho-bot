# -*- coding: utf-8 -*-
"""
Handlers para comandos adicionais
"""

from telegram import Update
from telegram.ext import ContextTypes
from config import *
from database.db_manager import DatabaseManager
from handlers import shop_handlers, admin_handlers


async def novo_pedido_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: DatabaseManager):
    """Handler para o comando /novo_pedido"""
    return await shop_handlers.new_request(update, context, db)


async def meus_pedidos_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: DatabaseManager):
    """Handler para o comando /meus_pedidos"""
    return await shop_handlers.my_requests(update, context, db)


async def pendentes_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: DatabaseManager):
    """Handler para o comando /pendentes"""
    telegram_id = update.effective_user.id
    
    if telegram_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Apenas administradores podem usar este comando.")
        return
    
    return await admin_handlers.pending_requests(update, context, db)


async def todos_pedidos_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: DatabaseManager):
    """Handler para o comando /todos_pedidos"""
    telegram_id = update.effective_user.id
    
    if telegram_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Apenas administradores podem usar este comando.")
        return
    
    return await admin_handlers.all_requests(update, context, db)


async def estatisticas_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: DatabaseManager):
    """Handler para o comando /estatisticas"""
    telegram_id = update.effective_user.id
    
    if telegram_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Apenas administradores podem usar este comando.")
        return
    
    # Obter estatísticas
    stats = db.get_statistics()
    
    message = f"""
📊 **Estatísticas do Sistema**

📝 Total de Pedidos: {stats['total']}
⏳ Pendentes: {stats['pending']}
✅ Aprovados: {stats['approved']}
❌ Rejeitados: {stats['rejected']}
"""
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: DatabaseManager):
    """Handler para o comando /menu"""
    telegram_id = update.effective_user.id
    db_user = db.get_user(telegram_id)
    
    if telegram_id in ADMIN_IDS or (db_user and db_user['is_admin']):
        await admin_handlers.show_admin_menu(update, context)
        return ADMIN_MENU
    else:
        await shop_handlers.show_shop_menu(update, context)
        return MAIN_MENU
