# -*- coding: utf-8 -*-
"""
Comandos para bloqueio de dias e gestão de agendamentos
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import sqlite3
from datetime import datetime
from visual_calendar import create_visual_calendar
import logging

logger = logging.getLogger(__name__)

DB_PATH = "database/hugo_bot.db"
ADMIN_IDS = [789741735, 615966323, 228613920]


def get_db():
    """Conectar à base de dados"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


async def bloquear_dia_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /bloquear_dia - Bloquear período (admin)"""
    try:
        user_id = update.effective_user.id
        logger.info(f"📦 /bloquear_dia chamado por user_id={user_id}")
        
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("❌ Você não tem permissão para usar este comando.")
            return
        
        # Mostrar calendário para seleção
        calendar = create_visual_calendar()
        logger.info(f"✅ Calendário criado")
        
        # Guardar estado na BD
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM temp_states WHERE user_id = ?', (user_id,))
        cursor.execute('INSERT INTO temp_states (user_id, state_data) VALUES (?, ?)', (user_id, 'blocking_start'))
        conn.commit()
        conn.close()
        logger.info(f"✅ Estado guardado na BD")
        
        await update.message.reply_text(
            "🚫 **Bloquear Período**\n\n"
            "📅 Selecione a data de **INÍCIO** do bloqueio:",
            reply_markup=calendar,
            parse_mode='Markdown'
        )
        logger.info(f"✅ Mensagem enviada")
    except Exception as e:
        logger.error(f"❌ ERRO em bloquear_dia_command: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Erro: {str(e)}")


async def desbloquear_dia_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /desbloquear_dia - Remover bloqueios (admin)"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Você não tem permissão para usar este comando.")
        return
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Buscar bloqueios ativos
    cursor.execute('''
        SELECT id, start_date, end_date, period, reason
        FROM blocked_dates
        WHERE end_date >= date('now')
        ORDER BY start_date ASC
    ''')
    
    bloqueios = cursor.fetchall()
    conn.close()
    
    if not bloqueios:
        await update.message.reply_text("ℹ️ Não há bloqueios ativos.")
        return
    
    # Inicializar lista de selecionados
    context.user_data['unblock_selected'] = []
    context.user_data['unblock_list'] = [dict(b) for b in bloqueios]
    
    keyboard = []
    for bloqueio in bloqueios:
        start_date_obj = datetime.strptime(bloqueio['start_date'], '%Y-%m-%d')
        end_date_obj = datetime.strptime(bloqueio['end_date'], '%Y-%m-%d')
        
        if bloqueio['start_date'] == bloqueio['end_date']:
            date_pt = start_date_obj.strftime('%d/%m/%Y')
        else:
            date_pt = f"{start_date_obj.strftime('%d/%m/%Y')} - {end_date_obj.strftime('%d/%m/%Y')}"
        
        periodo_emoji = "🌅" if bloqueio['period'] == "Manhã" else ("🌆" if bloqueio['period'] == "Tarde" else "📆")
        
        text = f"◻ {date_pt} - {periodo_emoji} {bloqueio['period']}"
        if bloqueio['reason']:
            text += f" ({bloqueio['reason']})"
        
        keyboard.append([InlineKeyboardButton(
            text,
            callback_data=f"toggle_unblock_{bloqueio['id']}"
        )])
    
    keyboard.append([
        InlineKeyboardButton("✅ Confirmar Remoção", callback_data="confirm_unblock"),
        InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")
    ])
    
    await update.message.reply_text(
        "🔓 **Desbloquear Período**\n\n"
        "Selecione os bloqueios que deseja remover (múltipla seleção):\n"
        "◻ = Não selecionado | ✅ = Selecionado",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def gerir_pedidos_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /gerir_pedidos - Listar e gerir pedidos aprovados (admin)"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Você não tem permissão para usar este comando.")
        return
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Buscar pedidos aprovados futuros
    cursor.execute('''
        SELECT r.id, r.start_date, r.period, r.request_type, u.shop_name
        FROM requests r
        JOIN users u ON r.shop_telegram_id = u.telegram_id
        WHERE r.status = 'Aprovado' AND r.start_date >= date('now')
        ORDER BY r.start_date ASC, r.period ASC
        LIMIT 20
    ''')
    
    pedidos = cursor.fetchall()
    conn.close()
    
    if not pedidos:
        await update.message.reply_text("ℹ️ Não há pedidos aprovados futuros.")
        return
    
    keyboard = []
    for pedido in pedidos:
        date_obj = datetime.strptime(pedido['start_date'], '%Y-%m-%d')
        date_pt = date_obj.strftime('%d/%m/%Y')
        
        periodo_emoji = "🌅" if pedido['period'] == "Manhã" else ("🌆" if pedido['period'] == "Tarde" else "📆")
        
        text = f"{date_pt} - {pedido['shop_name']} - {periodo_emoji} {pedido['period']}"
        
        keyboard.append([InlineKeyboardButton(
            text,
            callback_data=f"gerir_{pedido['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("❌ Fechar", callback_data="cancelar")])
    
    await update.message.reply_text(
        "🗂️ **Gerir Pedidos Aprovados**\n\n"
        "Selecione um pedido para editar ou cancelar:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
