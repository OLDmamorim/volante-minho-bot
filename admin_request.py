# -*- coding: utf-8 -*-
"""
Módulo para criação de pedidos por administradores
Usa o mesmo fluxo do /pedido normal, mas automaticamente para loja "Volante"
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import sqlite3
import logging

logger = logging.getLogger(__name__)

DB_PATH = "database/hugo_bot.db"
VOLANTE_SHOP_ID = 999999999  # ID especial para loja Volante

def get_db():
    """Conectar à base de dados"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

async def admin_create_request_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Iniciar criação de pedido por admin
    Primeiro pede tipo, depois (se for Apoio) pede a loja
    """
    
    # Marcar que é um pedido admin
    context.user_data['is_admin_request'] = True
    
    # Mostrar tipos de pedido
    keyboard = [
        [InlineKeyboardButton("🔧 Apoio", callback_data="admin_tipo_Apoio")],
        [InlineKeyboardButton("🏬 Volante (Férias/Outros)", callback_data="admin_tipo_Volante")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👑 **Criar Pedido Admin**\n\n"
        "Selecione o tipo de pedido:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancelar operação"""
    await update.message.reply_text("❌ Operação cancelada.")
    context.user_data.clear()


async def handle_admin_tipo_apoio(query):
    """Mostrar lista de lojas para selecionar apoio"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Buscar todas as lojas (exceto Volante)
    cursor.execute('''
        SELECT telegram_id, shop_name, username
        FROM users
        WHERE telegram_id != ?
        ORDER BY shop_name ASC
    ''', (VOLANTE_SHOP_ID,))
    
    shops = cursor.fetchall()
    conn.close()
    
    if not shops:
        await query.edit_message_text("❌ Não há lojas registadas para apoio.")
        return
    
    keyboard = []
    for shop in shops:
        shop_name = shop['shop_name'] or shop['username'] or 'Sem nome'
        keyboard.append([InlineKeyboardButton(
            f"🏬 {shop_name}",
            callback_data=f"admin_shop_{shop['telegram_id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")])
    
    await query.edit_message_text(
        "🔧 **Apoio a Loja**\n\n"
        "Selecione a loja que vai receber o apoio:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def handle_admin_tipo_volante(query, context):
    """Configurar pedido para loja Volante (Férias/Outros)"""
    context.user_data['admin_request_shop_id'] = VOLANTE_SHOP_ID
    context.user_data['admin_request_shop_name'] = 'Volante'
    
    # Mostrar tipos de pedido (Férias/Outros)
    keyboard = [
        [InlineKeyboardButton("🏖️ Férias", callback_data="tipo_Férias")],
        [InlineKeyboardButton("📋 Outros", callback_data="tipo_Outros")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
    ]
    
    await query.edit_message_text(
        "👑 **Novo Pedido para Volante**\n\n"
        "🏬 Loja: **Volante**\n\n"
        "Selecione o tipo de pedido:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def handle_admin_shop_selection(query, context, shop_id: int):
    """Processar seleção de loja para apoio"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT shop_name, username FROM users WHERE telegram_id = ?', (shop_id,))
    shop = cursor.fetchone()
    conn.close()
    
    if not shop:
        await query.edit_message_text("❌ Loja não encontrada.")
        return
    
    shop_name = shop['shop_name'] or shop['username'] or 'Sem nome'
    
    # Configurar pedido para esta loja
    context.user_data['admin_request_shop_id'] = shop_id
    context.user_data['admin_request_shop_name'] = shop_name
    context.user_data['request_type'] = 'Apoio'
    
    logger.info(f"✅ Admin criando apoio para loja {shop_name} (ID: {shop_id})")
    
    # Importar e mostrar calendário
    from visual_calendar import create_visual_calendar
    calendar = create_visual_calendar()
    
    await query.edit_message_text(
        f"🔧 **Apoio a {shop_name}**\n\n"
        f"📅 Selecione a data do apoio:",
        reply_markup=calendar,
        parse_mode='Markdown'
    )
