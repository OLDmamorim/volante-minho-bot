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
    Usa o mesmo fluxo do /pedido normal, mas marca como pedido admin para loja Volante
    """
    
    # Marcar que é um pedido admin (para loja Volante)
    context.user_data['is_admin_request'] = True
    context.user_data['admin_request_shop_id'] = VOLANTE_SHOP_ID
    context.user_data['admin_request_shop_name'] = 'Volante'
    
    # Mostrar tipos de pedido (igual ao /pedido normal)
    keyboard = [
        [InlineKeyboardButton("🔧 Apoio", callback_data="tipo_Apoio")],
        [InlineKeyboardButton("🏖️ Férias", callback_data="tipo_Férias")],
        [InlineKeyboardButton("📋 Outros", callback_data="tipo_Outros")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👑 **Novo Pedido para Volante**\n\n"
        "🏬 Loja: **Volante**\n\n"
        "Selecione o tipo de pedido:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancelar operação"""
    await update.message.reply_text("❌ Operação cancelada.")
    context.user_data.clear()
