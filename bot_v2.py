# -*- coding: utf-8 -*-
"""
Bot Volante Minho 2.0 - Versão Completa com Calendário Visual e Férias com Período
"""
import logging
import sqlite3
from datetime import datetime, timedelta
import os
from sync_mysql import sync_request_to_mysql, sync_user_to_mysql
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from calendar_helper import TelegramCalendar
from visual_calendar import create_visual_calendar, process_calendar_callback
from calendar_links import generate_calendar_links, create_calendar_buttons
from block_and_manage import bloquear_dia_command, desbloquear_dia_command, gerir_pedidos_command
from reminders import setup_reminders
from admin_request import admin_create_request_start, admin_cancel
from dashboard_sync import setup_dashboard_sync
from export_stats import generate_stats_excel
from export_command import exportar_estatisticas_command

# Configuração
BOT_TOKEN = "8365753572:AAGiZrUoYxxfYlrRWZaIwNGkKiWQ_EzdX78"
ADMIN_IDS = [789741735, 615966323, 228613920]
DB_PATH = "database/hugo_bot.db"

# Criar diretório da base de dados se não existir
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Função para inicializar a base de dados
def init_database():
    """Inicializa as tabelas da base de dados"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabela de utilizadores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            is_admin BOOLEAN NOT NULL DEFAULT FALSE,
            shop_name TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de pedidos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_telegram_id INTEGER NOT NULL,
            request_type TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE,
            period TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pendente',
            rejection_reason TEXT,
            observations TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP,
            processed_by INTEGER,
            FOREIGN KEY (shop_telegram_id) REFERENCES users (telegram_id),
            FOREIGN KEY (processed_by) REFERENCES users (telegram_id)
        )
    ''')
    
    # Tabela de notificações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER,
            recipient_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (request_id) REFERENCES requests (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Inicializar base de dados
init_database()

# Estados do ConversationHandler
AWAITING_SHOP_NAME = 1

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_db():
    """Conectar à base de dados"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    user_id = update.effective_user.id
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar se usuário existe
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        # Novo usuário
        if user_id in ADMIN_IDS:
            # Admin
            cursor.execute('''
                INSERT INTO users (telegram_id, is_admin, shop_name)
                VALUES (?, 1, ?)
            ''', (user_id, 'Admin'))
            conn.commit()
            conn.close()
            
            await update.message.reply_text(
                "👋 Bem-vindo, Administrador!\n\n"
                "Use os comandos para gerir pedidos.",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            # Loja - pedir nome
            conn.close()
            await update.message.reply_text(
                "👋 Bem-vindo ao sistema de pedidos!\n\n"
                "Por favor, indique o nome da sua loja:"
            )
            return AWAITING_SHOP_NAME
    else:
        # Usuário existente
        conn.close()
        
        if user_id in ADMIN_IDS:
            await update.message.reply_text(
                f"👋 Bem-vindo de volta, Administrador!\n\n"
                "O que deseja fazer?",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await update.message.reply_text(
                f"👋 Bem-vindo de volta, {user['shop_name']}!\n\n"
                "O que deseja fazer?",
                reply_markup=ReplyKeyboardRemove()
            )
    
    return ConversationHandler.END


async def receive_shop_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receber nome da loja"""
    shop_name = update.message.text.strip()
    user_id = update.effective_user.id
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO users (telegram_id, shop_name, is_admin)
        VALUES (?, ?, 0)
    ''', (user_id, shop_name))
    
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ Loja '{shop_name}' registada com sucesso!")
    await start(update, context)
    return ConversationHandler.END


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
        [InlineKeyboardButton("🔧 Apoio", callback_data="tipo_Apoio")],
        [InlineKeyboardButton("🏖️ Férias", callback_data="tipo_Férias")],
        [InlineKeyboardButton("📋 Outros", callback_data="tipo_Outros")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📝 **Novo Pedido**\n\nSelecione o tipo de pedido:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para callbacks dos botões"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Cancelar
    if data == "cancelar":
        await query.edit_message_text("❌ Operação cancelada.")
        context.user_data.clear()
        return
    
    # Tipo de pedido
    if data.startswith("tipo_"):
        tipo = data.replace("tipo_", "")
        context.user_data['request_type'] = tipo
        logger.info(f"Tipo selecionado: {tipo}, is_admin_request: {context.user_data.get('is_admin_request', False)}")
        
        # Mostrar calendário VISUAL com cores
        if tipo == "Férias":
            context.user_data['selecting_vacation_start'] = True
            calendar_markup = create_visual_calendar()
            await query.edit_message_text(
                f"📝 Tipo: **{tipo}**\n\n"
                f"🏖️ **Selecione a data de INÍCIO das férias:**\n\n"
                "🟢 Disponível | 🔴 Ocupado | 🟣 Manhã | 🔵 Tarde | 🟡 Pendente",
                reply_markup=calendar_markup,
                parse_mode='Markdown'
            )
        else:
            calendar_markup = create_visual_calendar()
            await query.edit_message_text(
                f"📝 Tipo: **{tipo}**\n\n"
                f"📅 **Selecione a data:**\n\n"
                "🟢 Disponível | 🔴 Ocupado | 🟣 Manhã | 🔵 Tarde | 🟡 Pendente",
                reply_markup=calendar_markup,
                parse_mode='Markdown'
            )
        return
    
    # Calendário Visual no fluxo de pedidos
    if data.startswith("cal_day_"):
        parts = data.split('_')
        year = int(parts[2])
        month = int(parts[3])
        day = int(parts[4])
        
        date_str = f"{year:04d}-{month:02d}-{day:02d}"
        date_pt = f"{day:02d}/{month:02d}/{year:04d}"
        logger.info(f"Data selecionada: {date_str}, context.user_data keys: {list(context.user_data.keys())}")
        
        # Verificar se está a bloquear período (início)
        if context.user_data.get('blocking_start'):
            context.user_data['blocking_start'] = False
            context.user_data['blocking_end'] = True
            context.user_data['block_start_date'] = date_str
            context.user_data['block_start_date_pt'] = date_pt
            
            calendar_markup = create_visual_calendar()
            await query.edit_message_text(
                f"🚫 **Bloquear Período**\n\n"
                f"📅 Início: **{date_pt}**\n\n"
                f"📅 Selecione a data de **FIM** do bloqueio:",
                reply_markup=calendar_markup,
                parse_mode='Markdown'
            )
            return
        
        # Verificar se está a bloquear período (fim)
        if context.user_data.get('blocking_end'):
            context.user_data['blocking_end'] = False
            context.user_data['block_end_date'] = date_str
            context.user_data['block_end_date_pt'] = date_pt
            
            # Pedir período para bloquear
            keyboard = [
                [InlineKeyboardButton("🌅 Manhã", callback_data="block_period_Manhã")],
                [InlineKeyboardButton("🌆 Tarde", callback_data="block_period_Tarde")],
                [InlineKeyboardButton("📆 Todo o dia", callback_data="block_period_Todo o dia")],
                [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
            ]
            
            await query.edit_message_text(
                f"🚫 **Bloquear Período**\n\n"
                f"📅 Início: **{context.user_data['block_start_date_pt']}**\n"
                f"📅 Fim: **{date_pt}**\n\n"
                f"Selecione o período a bloquear:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        # Verificar se é férias
        if context.user_data.get('selecting_vacation_start'):
            # Primeira data (início)
            context.user_data['vacation_start'] = date_str
            context.user_data['vacation_start_pt'] = date_pt
            context.user_data['selecting_vacation_start'] = False
            context.user_data['selecting_vacation_end'] = True
            
            calendar_markup = create_visual_calendar()
            await query.edit_message_text(
                f"📝 Tipo: **{context.user_data['request_type']}**\n"
                f"📅 Início: **{date_pt}**\n\n"
                f"🏖️ **Selecione a data de FIM das férias:**\n\n"
                "🟢 Disponível | 🔴 Ocupado | 🟣 Manhã | 🔵 Tarde | 🟡 Pendente",
                reply_markup=calendar_markup,
                parse_mode='Markdown'
            )
            return
            
        elif context.user_data.get('selecting_vacation_end'):
            # Segunda data (fim)
            context.user_data['vacation_end'] = date_str
            context.user_data['vacation_end_pt'] = date_pt
            context.user_data['selecting_vacation_end'] = False
            
            # Pedir observações
            await query.edit_message_text(
                f"📝 Tipo: **{context.user_data['request_type']}**\n"
                f"📅 Início: **{context.user_data['vacation_start_pt']}**\n"
                f"📅 Fim: **{context.user_data['vacation_end_pt']}**\n\n"
                f"📝 Observações? (ou envie \"não\" para pular)",
                parse_mode='Markdown'
            )
            
            context.user_data['awaiting_observations'] = True
            context.user_data['is_vacation'] = True
            return
        
        else:
            # Pedido normal (não férias)
            context.user_data['date'] = date_str
            context.user_data['date_pt'] = date_pt
            
            # Verificar disponibilidade de períodos
            status = get_day_status(year, month, day)
            
            # Construir teclado baseado na disponibilidade
            keyboard = []
            
            if status == 'disponivel':
                # Dia totalmente disponível
                keyboard.append([InlineKeyboardButton("🌅 Manhã", callback_data="periodo_Manhã")])
                keyboard.append([InlineKeyboardButton("🌆 Tarde", callback_data="periodo_Tarde")])
                keyboard.append([InlineKeyboardButton("📆 Todo o dia", callback_data="periodo_Todo o dia")])
            elif status == 'ocupado_manha':
                # Manhã ocupada, só tarde disponível
                keyboard.append([InlineKeyboardButton("🌆 Tarde", callback_data="periodo_Tarde")])
            elif status == 'ocupado_tarde':
                # Tarde ocupada, só manhã disponível
                keyboard.append([InlineKeyboardButton("🌅 Manhã", callback_data="periodo_Manhã")])
            elif status == 'pendente':
                # Há pedidos pendentes, mostrar aviso
                await query.edit_message_text(
                    f"⚠️ **Atenção!**\n\n"
                    f"📅 Data: **{date_pt}**\n\n"
                    f"Há pedidos pendentes para este dia. Aguarde a aprovação ou escolha outra data.",
                    parse_mode='Markdown'
                )
                return
            
            keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"📝 Tipo: **{context.user_data.get('request_type')}**\n"
                f"📅 Data: **{date_pt}**\n\n"
                f"Selecione o período:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
    
    # Navegação do calendário visual
    if data.startswith("cal_prev_") or data.startswith("cal_next_"):
        result = process_calendar_callback(data)
        _, year, month = result
        calendar_markup = create_visual_calendar(year, month)
        
        # Manter mensagem apropriada
        if context.user_data.get('selecting_vacation_start'):
            msg = (f"📝 Tipo: **{context.user_data['request_type']}**\n\n"
                   f"🏖️ **Selecione a data de INÍCIO das férias:**\n\n"
                   "🟢 Disponível | 🔴 Ocupado | 🟣 Manhã | 🔵 Tarde | 🟡 Pendente")
        elif context.user_data.get('selecting_vacation_end'):
            msg = (f"📝 Tipo: **{context.user_data['request_type']}**\n"
                   f"📅 Início: **{context.user_data['vacation_start_pt']}**\n\n"
                   f"🏖️ **Selecione a data de FIM das férias:**\n\n"
                   "🟢 Disponível | 🔴 Ocupado | 🟣 Manhã | 🔵 Tarde | 🟡 Pendente")
        elif context.user_data.get('request_type'):
            msg = (f"📝 Tipo: **{context.user_data.get('request_type')}**\n\n"
                   f"📅 **Selecione a data:**\n\n"
                   "🟢 Disponível | 🔴 Ocupado | 🟣 Manhã | 🔵 Tarde | 🟡 Pendente")
        else:
            # Navegação no comando /calendario (sem pedido ativo)
            month_names = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                           'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
            msg = (f"📅 **Calendário de Pedidos - {month_names[month]} {year}**\n\n"
                   f"🟢 Disponível | 🔴 Ocupado todo o dia\n"
                   f"🟣 Manhã ocupada | 🔵 Tarde ocupada | 🟡 Pendente")
        
        await query.edit_message_text(
            msg,
            reply_markup=calendar_markup,
            parse_mode='Markdown'
        )
        return
    
    # Fechar calendário
    if data == "cal_close":
        await query.edit_message_text("✅ Calendário fechado.")
        context.user_data.clear()
        return
    
    # Bloqueio de período
    if data.startswith("block_period_"):
        periodo = data.replace("block_period_", "")
        admin_id = query.from_user.id
        
        # Pedir motivo do bloqueio
        context.user_data['block_period'] = periodo
        
        await query.edit_message_text(
            f"🚫 **Bloquear Período**\n\n"
            f"📅 De: **{context.user_data['block_start_date_pt']}**\n"
            f"📅 Até: **{context.user_data['block_end_date_pt']}**\n"
            f"🕐 Período: **{periodo}**\n\n"
            f"📝 Por favor, envie o motivo do bloqueio (ou \"não\" para pular):",
            parse_mode='Markdown'
        )
        
        context.user_data['awaiting_block_reason'] = True
        return
    
    # Período
    if data.startswith("periodo_"):
        periodo = data.replace("periodo_", "")
        context.user_data['period'] = periodo
        
        # Pedir observações
        logger.info(f"Antes de pedir observações - context.user_data: {dict(context.user_data)}")
        await query.edit_message_text(
            f"📝 Tipo: **{context.user_data.get('request_type')}**\n"
            f"📅 Data: **{context.user_data.get('date_pt')}**\n"
            f"🕐 Período: **{periodo}**\n\n"
            f"📝 Observações? (ou envie \"não\" para pular)",
            parse_mode='Markdown'
        )
        
        context.user_data['awaiting_observations'] = True
        return
    
    # Aprovar pedido
    if data.startswith("aprovar_"):
        request_id = int(data.replace("aprovar_", ""))
        admin_id = query.from_user.id
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Atualizar pedido
        cursor.execute('''
            UPDATE requests 
            SET status = 'Aprovado', processed_at = ?, processed_by = ?
            WHERE id = ?
        ''', (datetime.now(), admin_id, request_id))
        
        # Buscar info do pedido
        cursor.execute('''
            SELECT r.*, u.shop_name 
            FROM requests r
            JOIN users u ON r.shop_telegram_id = u.telegram_id
            WHERE r.id = ?
        ''', (request_id,))
        req = cursor.fetchone()
        
        conn.commit()
        
        # Sincronizar com MySQL
        try:
            sync_request_to_mysql(
                request_id=request_id,
                shop_telegram_id=req['shop_telegram_id'],
                shop_name=req['shop_name'],
                request_type=req['request_type'],
                start_date=req['start_date'],
                end_date=req['start_date'],  # Para pedidos simples, end_date = start_date
                period=req['period'],
                status='approved',
                rejection_reason=None,
                created_at=req.get('created_at')
            )
            logger.info(f"Pedido {request_id} sincronizado com MySQL (aprovado)")
        except Exception as e:
            logger.error(f"Erro ao sincronizar pedido aprovado: {e}")
        
        conn.close()
        
        # Gerar links de calendário
        try:
            observations = req['observations'] if req['observations'] else ''
        except (KeyError, IndexError):
            observations = ''
        
        request_data = {
            'shop_name': req['shop_name'],
            'request_type': req['request_type'],
            'start_date': req['start_date'],
            'period': req['period'],
            'observations': observations
        }
        
        google_url, ics_content = generate_calendar_links(request_data)
        calendar_buttons = create_calendar_buttons(google_url)
        
        # Notificar loja
        try:
            await context.bot.send_message(
                chat_id=req['shop_telegram_id'],
                text=f"✅ **Pedido Aprovado!**\n\n"
                     f"📝 Tipo: {req['request_type']}\n"
                     f"📅 Data: {req['start_date']}\n"
                     f"🕐 Período: {req['period']}",
                parse_mode='Markdown'
            )
        except:
            pass
        
        await query.edit_message_text(
            f"✅ **Pedido #{request_id} Aprovado!**\n\n"
            f"🏬 Loja: {req['shop_name']}\n"
            f"📝 Tipo: {req['request_type']}\n"
            f"📅 Data: {req['start_date']}\n"
            f"🕐 Período: {req['period']}\n\n"
            f"📅 **Adicionar ao Calendário:**",
            reply_markup=calendar_buttons,
            parse_mode='Markdown'
        )
        
        # Atualizar mensagens dos outros admins
        import json
        logger.info(f"Tentando atualizar mensagens dos outros admins para pedido #{request_id}")
        admin_msg_ids = req['admin_message_ids'] if 'admin_message_ids' in req.keys() else None
        if admin_msg_ids:
            try:
                admin_messages = json.loads(admin_msg_ids)
                admin_name = query.from_user.first_name or "Admin"
                logger.info(f"admin_message_ids encontrado: {admin_messages}, admin que aprovou: {admin_id}")
                
                for other_admin_id, message_id in admin_messages.items():
                    other_admin_id = int(other_admin_id)
                    if other_admin_id != admin_id:  # Não atualizar a mensagem do admin que aprovou
                        try:
                            logger.info(f"Atualizando mensagem {message_id} para admin {other_admin_id}")
                            await context.bot.edit_message_text(
                                chat_id=other_admin_id,
                                message_id=message_id,
                                text=f"✅ **Pedido #{request_id} Aprovado por {admin_name}**\n\n"
                                     f"🏬 Loja: {req['shop_name']}\n"
                                     f"📝 Tipo: {req['request_type']}\n"
                                     f"📅 Data: {req['start_date']}\n"
                                     f"🕐 Período: {req['period']}",
                                parse_mode='Markdown'
                            )
                            logger.info(f"Mensagem {message_id} atualizada com sucesso")
                        except Exception as e:
                            logger.error(f"Erro ao atualizar mensagem {message_id}: {e}")
            except Exception as e:
                logger.error(f"Erro ao processar admin_message_ids: {e}")
        else:
            logger.warning(f"Pedido #{request_id} não tem admin_message_ids")
        
        return
    
    # Rejeitar pedido
    if data.startswith("rejeitar_"):
        request_id = int(data.replace("rejeitar_", ""))
        context.user_data['rejecting_request_id'] = request_id
        
        await query.edit_message_text(
            "❌ **Rejeitar Pedido**\n\n"
            "Por favor, envie o motivo da rejeição:"
        )
        context.user_data['awaiting_rejection_reason'] = True
        return
    
    # Toggle seleção de bloqueio
    if data.startswith("toggle_unblock_"):
        bloqueio_id = int(data.replace("toggle_unblock_", ""))
        
        # Adicionar ou remover da lista de selecionados
        if bloqueio_id in context.user_data.get('unblock_selected', []):
            context.user_data['unblock_selected'].remove(bloqueio_id)
        else:
            context.user_data.setdefault('unblock_selected', []).append(bloqueio_id)
        
        # Reconstruir teclado com checkboxes atualizados
        keyboard = []
        for bloqueio in context.user_data.get('unblock_list', []):
            date_obj = datetime.strptime(bloqueio['date'], '%Y-%m-%d')
            date_pt = date_obj.strftime('%d/%m/%Y')
            
            periodo_emoji = "🌅" if bloqueio['period'] == "Manhã" else ("🌆" if bloqueio['period'] == "Tarde" else "📆")
            
            is_selected = bloqueio['id'] in context.user_data.get('unblock_selected', [])
            checkbox = "✅" if is_selected else "◻"
            
            text = f"{checkbox} {date_pt} - {periodo_emoji} {bloqueio['period']}"
            if bloqueio.get('reason'):
                text += f" ({bloqueio['reason']})"
            
            keyboard.append([InlineKeyboardButton(
                text,
                callback_data=f"toggle_unblock_{bloqueio['id']}"
            )])
        
        keyboard.append([
            InlineKeyboardButton("✅ Confirmar Remoção", callback_data="confirm_unblock"),
            InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")
        ])
        
        selected_count = len(context.user_data.get('unblock_selected', []))
        
        await query.edit_message_text(
            f"🔓 **Desbloquear Período**\n\n"
            f"Selecione os bloqueios que deseja remover (múltipla seleção):\n"
            f"◻ = Não selecionado | ✅ = Selecionado\n\n"
            f"📊 Selecionados: **{selected_count}**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return
    
    # Confirmar desbloqueio múltiplo
    if data == "confirm_unblock":
        selected_ids = context.user_data.get('unblock_selected', [])
        
        if not selected_ids:
            await query.answer("⚠️ Nenhum bloqueio selecionado!", show_alert=True)
            return
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Remover bloqueios selecionados
        placeholders = ','.join('?' * len(selected_ids))
        cursor.execute(f'DELETE FROM blocked_dates WHERE id IN ({placeholders})', selected_ids)
        conn.commit()
        conn.close()
        
        await query.edit_message_text(
            f"✅ **Bloqueios Removidos!**\n\n"
            f"📊 Total removido: **{len(selected_ids)}** bloqueios",
            parse_mode='Markdown'
        )
        
        context.user_data.pop('unblock_selected', None)
        context.user_data.pop('unblock_list', None)
        return
    
    # Gerir pedido
    if data.startswith("gerir_"):
        request_id = int(data.replace("gerir_", ""))
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.*, u.shop_name
            FROM requests r
            JOIN users u ON r.shop_telegram_id = u.telegram_id
            WHERE r.id = ?
        ''', (request_id,))
        
        pedido = cursor.fetchone()
        conn.close()
        
        if pedido:
            date_obj = datetime.strptime(pedido['start_date'], '%Y-%m-%d')
            date_pt = date_obj.strftime('%d/%m/%Y')
            
            keyboard = [
                [InlineKeyboardButton("🗑️ Cancelar Pedido", callback_data=f"cancelar_pedido_{request_id}")],
                [InlineKeyboardButton("❌ Voltar", callback_data="cancelar")]
            ]
            
            await query.edit_message_text(
                f"📝 **Detalhes do Pedido #{request_id}**\n\n"
                f"🏬 Loja: {pedido['shop_name']}\n"
                f"📝 Tipo: {pedido['request_type']}\n"
                f"📅 Data: {date_pt}\n"
                f"🕐 Período: {pedido['period']}\n\n"
                f"Escolha uma ação:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("❌ Pedido não encontrado.")
        
        return
    
    # Cancelar pedido
    if data.startswith("cancelar_pedido_"):
        request_id = int(data.replace("cancelar_pedido_", ""))
        admin_id = query.from_user.id
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Buscar info do pedido
        cursor.execute('''
            SELECT r.*, u.shop_name
            FROM requests r
            JOIN users u ON r.shop_telegram_id = u.telegram_id
            WHERE r.id = ?
        ''', (request_id,))
        
        pedido = cursor.fetchone()
        
        if pedido:
            # Atualizar status para cancelado
            cursor.execute('''
                UPDATE requests
                SET status = 'Cancelado', processed_at = ?, processed_by = ?
                WHERE id = ?
            ''', (datetime.now(), admin_id, request_id))
            
            conn.commit()
            
            # Notificar loja
            try:
                await context.bot.send_message(
                    chat_id=pedido['shop_telegram_id'],
                    text=f"❌ **Pedido Cancelado**\n\n"
                         f"📝 Tipo: {pedido['request_type']}\n"
                         f"📅 Data: {pedido['start_date']}\n"
                         f"🕐 Período: {pedido['period']}\n\n"
                         f"O pedido foi cancelado por um gestor.",
                    parse_mode='Markdown'
                )
            except:
                pass
            
            date_obj = datetime.strptime(pedido['start_date'], '%Y-%m-%d')
            date_pt = date_obj.strftime('%d/%m/%Y')
            
            await query.edit_message_text(
                f"✅ **Pedido #{request_id} Cancelado!**\n\n"
                f"🏬 Loja: {pedido['shop_name']}\n"
                f"📝 Tipo: {pedido['request_type']}\n"
                f"📅 Data: {date_pt}\n"
                f"🕐 Período: {pedido['period']}",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("❌ Pedido não encontrado.")
        
        conn.close()
        return


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para mensagens de texto"""
    text = update.message.text.strip()
    
    # Botão Menu
    if text == "≡ Menu" or text.lower() == "menu":
        await menu_command(update, context)
        return
    
    # Motivo de bloqueio
    if context.user_data.get('awaiting_block_reason'):
        context.user_data['awaiting_block_reason'] = False
        admin_id = update.effective_user.id
        
        reason = text if text.lower() != "não" else None
        
        # Calcular todos os dias do período
        from datetime import datetime, timedelta
        
        start_date = datetime.strptime(context.user_data['block_start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(context.user_data['block_end_date'], '%Y-%m-%d')
        
        conn = get_db()
        cursor = conn.cursor()
        
        blocked_count = 0
        already_blocked = 0
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            
            try:
                cursor.execute('''
                    INSERT INTO blocked_dates (date, period, reason, blocked_by)
                    VALUES (?, ?, ?, ?)
                ''', (
                    date_str,
                    context.user_data['block_period'],
                    reason,
                    admin_id
                ))
                blocked_count += 1
            except sqlite3.IntegrityError:
                already_blocked += 1
            
            current_date += timedelta(days=1)
        
        conn.commit()
        conn.close()
        
        # Mensagem de confirmação
        total_days = (end_date - start_date).days + 1
        
        msg = f"✅ **Período Bloqueado!**\n\n"
        msg += f"📅 De: {context.user_data['block_start_date_pt']}\n"
        msg += f"📅 Até: {context.user_data['block_end_date_pt']}\n"
        msg += f"🕐 Período: {context.user_data['block_period']}\n"
        msg += f"📝 Motivo: {reason or 'N/A'}\n\n"
        msg += f"📊 Total de dias: {total_days}\n"
        msg += f"✅ Bloqueados: {blocked_count}\n"
        
        if already_blocked > 0:
            msg += f"⚠️ Já bloqueados: {already_blocked}"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        
        context.user_data.clear()
        return
    
    # Observações
    if context.user_data.get('awaiting_observations'):
        context.user_data['awaiting_observations'] = False
        
        if text.lower() != "não":
            context.user_data['observations'] = text
        else:
            context.user_data['observations'] = ""
        
        # Verificar se é férias
        if context.user_data.get('is_vacation'):
            # Criar pedidos para cada dia do período
            start_date = datetime.strptime(context.user_data['vacation_start'], '%Y-%m-%d')
            end_date = datetime.strptime(context.user_data['vacation_end'], '%Y-%m-%d')
            
            user_id = update.effective_user.id
            request_type = context.user_data['request_type']
            observations = context.user_data.get('observations', '')
            
            conn = get_db()
            cursor = conn.cursor()
            
            # Criar um pedido para cada dia
            current_date = start_date
            created_count = 0
            
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                
                cursor.execute('''
                    INSERT INTO requests (shop_telegram_id, request_type, start_date, period, observations, status)
                    VALUES (?, ?, ?, ?, ?, 'Pendente')
                ''', (user_id, request_type, date_str, 'Todo o dia', observations))
                
                created_count += 1
                current_date += timedelta(days=1)
            
            conn.commit()
            conn.close()
            
            # Notificar admins
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=f"🔔 **Novos Pedidos de Férias!**\n\n"
                             f"📝 Tipo: {request_type}\n"
                             f"📅 Período: {context.user_data['vacation_start_pt']} a {context.user_data['vacation_end_pt']}\n"
                             f"📊 Total: {created_count} dias",
                        parse_mode='Markdown'
                    )
                except:
                    pass
            
            await update.message.reply_text(
                f"✅ **Pedido de Férias Criado!**\n\n"
                f"📝 Tipo: {request_type}\n"
                f"📅 Período: {context.user_data['vacation_start_pt']} a {context.user_data['vacation_end_pt']}\n"
                f"📊 Total: {created_count} dias\n\n"
                f"Aguarde aprovação dos gestores.",
                parse_mode='Markdown'
            )
            
            context.user_data.clear()
            return
        
        # Pedido normal ou admin
        is_admin_request = context.user_data.get('is_admin_request', False)
        
        if is_admin_request:
            # Pedido admin - para loja Volante, já aprovado
            shop_id = context.user_data['admin_request_shop_id']
            shop_name = context.user_data['admin_request_shop_name']
            status = 'Aprovado'
            admin_id = update.effective_user.id
        else:
            # Pedido normal - para loja do usuário, pendente
            shop_id = update.effective_user.id
            status = 'Pendente'
            admin_id = None
        
        request_type = context.user_data['request_type']
        date = context.user_data['date']
        period = context.user_data['period']
        observations = context.user_data.get('observations', '')
        
        conn = get_db()
        cursor = conn.cursor()
        
        if is_admin_request:
            # Pedido admin já aprovado
            cursor.execute('''
                INSERT INTO requests (shop_telegram_id, request_type, start_date, period, observations, status, processed_at, processed_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (shop_id, request_type, date, period, observations, status, datetime.now(), admin_id))
        else:
            # Pedido normal pendente
            cursor.execute('''
                INSERT INTO requests (shop_telegram_id, request_type, start_date, period, observations, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (shop_id, request_type, date, period, observations, status))
        
        request_id = cursor.lastrowid
        
        if not is_admin_request:
            # Buscar nome da loja para pedido normal
            cursor.execute('SELECT shop_name FROM users WHERE telegram_id = ?', (shop_id,))
            user_data = cursor.fetchone()
            shop_name = user_data['shop_name']
        
        conn.commit()
        
        # Sincronizar com MySQL
        try:
            sync_request_to_mysql(
                request_id=request_id,
                shop_telegram_id=shop_id,
                shop_name=shop_name,
                request_type=request_type,
                start_date=date,
                end_date=date,
                period=period,
                status='approved' if is_admin_request else 'pending',
                rejection_reason=None,
                created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            logger.info(f"Pedido {request_id} sincronizado com MySQL ({'admin' if is_admin_request else 'normal'})")
        except Exception as e:
            logger.error(f"Erro ao sincronizar pedido: {e}")
        
        conn.close()
        
        # Notificar admins (apenas para pedidos normais)
        if not is_admin_request:
            import json
            admin_messages = {}  # {admin_id: message_id}
            
            for admin_id in ADMIN_IDS:
                keyboard = [
                    [InlineKeyboardButton("✅ Aprovar", callback_data=f"aprovar_{request_id}")],
                    [InlineKeyboardButton("❌ Rejeitar", callback_data=f"rejeitar_{request_id}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                try:
                    msg = await context.bot.send_message(
                        chat_id=admin_id,
                        text=f"🔔 **Novo Pedido #{request_id}**\n\n"
                             f"🏬 Loja: {shop_name}\n"
                             f"📝 Tipo: {request_type}\n"
                             f"📅 Data: {context.user_data['date_pt']}\n"
                             f"🕐 Período: {period}",
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                    admin_messages[str(admin_id)] = msg.message_id
                except:
                    pass
            
            # Guardar message_ids na base de dados
            if admin_messages:
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE requests SET admin_message_ids = ? WHERE id = ?',
                    (json.dumps(admin_messages), request_id)
                )
                conn.commit()
                conn.close()
        
        # Mensagem de confirmação
        if is_admin_request:
            # Gerar links de calendário para pedido admin
            request_data = {
                'shop_name': shop_name,
                'request_type': request_type,
                'start_date': date,
                'period': period,
                'observations': observations
            }
            
            google_url, ics_content = generate_calendar_links(request_data)
            calendar_buttons = create_calendar_buttons(google_url)
            
            await update.message.reply_text(
                f"✅ **Pedido Criado e Aprovado!**\n\n"
                f"🏬 Loja: {shop_name}\n"
                f"📝 Tipo: {request_type}\n"
                f"📅 Data: {context.user_data['date_pt']}\n"
                f"🕐 Período: {period}\n\n"
                f"👑 Pedido criado por administrador - Automaticamente aprovado.\n\n"
                f"📅 **Adicionar ao Calendário:**",
                reply_markup=calendar_buttons,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"✅ **Pedido Criado!**\n\n"
                f"📝 Tipo: {request_type}\n"
                f"📅 Data: {context.user_data['date_pt']}\n"
                f"🕐 Período: {period}\n\n"
                f"Aguarde aprovação dos gestores.",
                parse_mode='Markdown'
            )
        
        context.user_data.clear()
        return
    
    # Motivo de rejeição
    if context.user_data.get('awaiting_rejection_reason'):
        context.user_data['awaiting_rejection_reason'] = False
        request_id = context.user_data['rejecting_request_id']
        reason = text
        admin_id = update.effective_user.id
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE requests 
            SET status = 'Rejeitado', rejection_reason = ?, processed_at = ?, processed_by = ?
            WHERE id = ?
        ''', (reason, datetime.now(), admin_id, request_id))
        
        # Buscar info do pedido
        cursor.execute('''
            SELECT r.*, u.shop_name 
            FROM requests r
            JOIN users u ON r.shop_telegram_id = u.telegram_id
            WHERE r.id = ?
        ''', (request_id,))
        req = cursor.fetchone()
        
        conn.commit()
        
        # Sincronizar com MySQL
        try:
            sync_request_to_mysql(
                request_id=request_id,
                shop_telegram_id=req['shop_telegram_id'],
                shop_name=req['shop_name'],
                request_type=req['request_type'],
                start_date=req['start_date'],
                end_date=req['start_date'],
                period=req['period'],
                status='rejected',
                rejection_reason=reason,
                created_at=req.get('created_at')
            )
            logger.info(f"Pedido {request_id} sincronizado com MySQL (rejeitado)")
        except Exception as e:
            logger.error(f"Erro ao sincronizar pedido rejeitado: {e}")
        
        conn.close()
        
        # Notificar loja
        try:
            await context.bot.send_message(
                chat_id=req['shop_telegram_id'],
                text=f"❌ **Pedido Rejeitado**\n\n"
                     f"📝 Tipo: {req['request_type']}\n"
                     f"📅 Data: {req['start_date']}\n"
                     f"🕐 Período: {req['period']}\n\n"
                     f"**Motivo:** {reason}",
                parse_mode='Markdown'
            )
        except:
            pass
        
        await update.message.reply_text(
            f"✅ **Pedido #{request_id} Rejeitado**\n\n"
            f"🏬 Loja: {req['shop_name']}\n"
            f"📝 Tipo: {req['request_type']}\n"
            f"📅 Data: {req['start_date']}\n"
            f"🕐 Período: {req['period']}\n\n"
            f"**Motivo:** {reason}",
            parse_mode='Markdown'
        )
        
        # Atualizar mensagens dos outros admins
        import json
        admin_msg_ids = req['admin_message_ids'] if 'admin_message_ids' in req.keys() else None
        if admin_msg_ids:
            try:
                admin_messages = json.loads(admin_msg_ids)
                admin_name = update.effective_user.first_name or "Admin"
                
                for other_admin_id, message_id in admin_messages.items():
                    other_admin_id = int(other_admin_id)
                    if other_admin_id != admin_id:  # Não atualizar a mensagem do admin que rejeitou
                        try:
                            await context.bot.edit_message_text(
                                chat_id=other_admin_id,
                                message_id=message_id,
                                text=f"❌ **Pedido #{request_id} Rejeitado por {admin_name}**\n\n"
                                     f"🏬 Loja: {req['shop_name']}\n"
                                     f"📝 Tipo: {req['request_type']}\n"
                                     f"📅 Data: {req['start_date']}\n"
                                     f"🕐 Período: {req['period']}\n\n"
                                     f"**Motivo:** {reason}",
                                parse_mode='Markdown'
                            )
                        except:
                            pass
            except:
                pass
        
        context.user_data.clear()
        return


async def calendario_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /calendario - Mostrar calendário visual"""
    year = datetime.now().year
    month = datetime.now().month
    
    # Criar calendário visual
    calendar_markup = create_visual_calendar(year, month)
    
    month_names = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                   'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    
    await update.message.reply_text(
        f"📅 **Calendário de Pedidos - {month_names[month]} {year}**\n\n"
        f"🟢 Disponível | 🔴 Ocupado todo o dia\n"
        f"🟣 Manhã ocupada | 🔵 Tarde ocupada | 🟡 Pendente",
        reply_markup=calendar_markup,
        parse_mode='Markdown'
    )


async def meus_pedidos_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /meus_pedidos - Ver pedidos da loja"""
    user_id = update.effective_user.id
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM requests WHERE shop_telegram_id = ?
        ORDER BY start_date DESC LIMIT 10
    ''', (user_id,))
    
    requests = cursor.fetchall()
    conn.close()
    
    if not requests:
        await update.message.reply_text("📄 Você ainda não tem pedidos.")
        return
    
    text = "📋 **Meus Pedidos**\n\n"
    
    for req in requests:
        status_emoji = "⏳" if req['status'] == 'pending' else ("✅" if req['status'] == 'approved' else "❌")
        status_text = "Pendente" if req['status'] == 'pending' else ("Aprovado" if req['status'] == 'approved' else "Rejeitado")
        
        text += f"{status_emoji} **Pedido #{req['id']}**\n"
        text += f"📝 Tipo: {req['request_type']}\n"
        text += f"📅 Data: {req['start_date']}\n"
        text += f"🕐 Período: {req['period']}\n"
        text += f"🚦 Status: {status_text}\n\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')


async def minha_loja_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /minha_loja - Ver informações da loja"""
    user_id = update.effective_user.id
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        await update.message.reply_text("❌ Utilizador não encontrado.")
        conn.close()
        return
    
    # Contar pedidos
    cursor.execute('SELECT COUNT(*) as total FROM requests WHERE shop_telegram_id = ?', (user_id,))
    total = cursor.fetchone()['total']
    
    cursor.execute('SELECT COUNT(*) as pending FROM requests WHERE shop_telegram_id = ? AND status = "Pendente"', (user_id,))
    pending = cursor.fetchone()['pending']
    
    cursor.execute('SELECT COUNT(*) as approved FROM requests WHERE shop_telegram_id = ? AND status = "Aprovado"', (user_id,))
    approved = cursor.fetchone()['approved']
    
    conn.close()
    
    text = f"🏬 **Informações da Loja**\n\n"
    text += f"🏷️ Nome: {user['shop_name']}\n"
    text += f"🆔 ID: {user_id}\n\n"
    text += f"📊 **Estatísticas:**\n"
    text += f"📄 Total de pedidos: {total}\n"
    text += f"⏳ Pendentes: {pending}\n"
    text += f"✅ Aprovados: {approved}\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')


async def pendentes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /pendentes - Ver pedidos pendentes (admin)"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Você não tem permissão para usar este comando.")
        return
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT r.*, u.shop_name 
        FROM requests r
        JOIN users u ON r.shop_telegram_id = u.telegram_id
        WHERE r.status = 'Pendente'
        ORDER BY r.created_at ASC
    ''')
    
    requests = cursor.fetchall()
    conn.close()
    
    if not requests:
        await update.message.reply_text("✅ Não há pedidos pendentes!")
        return
    
    for req in requests:
        try:
            observations = req['observations'] if req['observations'] else 'Sem observações'
        except (KeyError, IndexError):
            observations = 'Sem observações'
        
        text = (
            f"⏳ **Pedido #{req['id']} - Pendente**\n\n"
            f"🏬 Loja: {req['shop_name']}\n"
            f"📝 Tipo: {req['request_type']}\n"
            f"📅 Data: {req['start_date']}\n"
            f"🕐 Período: {req['period']}\n"
            f"📝 Observações: {observations}"
        )
        
        keyboard = [
            [InlineKeyboardButton("✅ Aprovar", callback_data=f"aprovar_{req['id']}")],
            [InlineKeyboardButton("❌ Rejeitar", callback_data=f"rejeitar_{req['id']}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


async def estatisticas_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /estatisticas - Ver estatísticas (admin)"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Você não tem permissão para usar este comando.")
        return
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Total de pedidos
    cursor.execute('SELECT COUNT(*) as total FROM requests')
    total = cursor.fetchone()['total']
    
    # Por status
    cursor.execute('SELECT COUNT(*) as count FROM requests WHERE status = "Pendente"')
    pendentes = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM requests WHERE status = "Aprovado"')
    aprovados = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM requests WHERE status = "Rejeitado"')
    rejeitados = cursor.fetchone()['count']
    
    # Por tipo
    cursor.execute('SELECT request_type, COUNT(*) as count FROM requests GROUP BY request_type')
    tipos = cursor.fetchall()
    
    # Por período
    cursor.execute('SELECT period, COUNT(*) as count FROM requests GROUP BY period')
    periodos = cursor.fetchall()
    
    # Por loja (top 5)
    cursor.execute('''
        SELECT u.shop_name, COUNT(*) as count 
        FROM requests r
        JOIN users u ON r.shop_telegram_id = u.telegram_id
        GROUP BY u.shop_name
        ORDER BY count DESC
        LIMIT 5
    ''')
    lojas = cursor.fetchall()
    
    conn.close()
    
    text = "📊 **Estatísticas do Sistema**\n\n"
    text += f"📄 **Total de Pedidos:** {total}\n\n"
    
    text += "🚦 **Por Status:**\n"
    text += f"⏳ Pendentes: {pendentes}\n"
    text += f"✅ Aprovados: {aprovados}\n"
    text += f"❌ Rejeitados: {rejeitados}\n\n"
    
    text += "📝 **Por Tipo:**\n"
    for tipo in tipos:
        text += f"• {tipo['request_type']}: {tipo['count']}\n"
    text += "\n"
    
    text += "🕐 **Por Período:**\n"
    for periodo in periodos:
        text += f"• {periodo['period']}: {periodo['count']}\n"
    text += "\n"
    
    text += "🏬 **Top 5 Lojas:**\n"
    for loja in lojas:
        text += f"• {loja['shop_name']}: {loja['count']} pedidos\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')


async def agenda_semana_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /agenda_semana - Ver agenda da semana (admin)"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Você não tem permissão para usar este comando.")
        return
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Próximos 7 dias
    today = datetime.now().date()
    dates = [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    
    text = "📅 **Agenda da Semana**\n\n"
    
    for date_str in dates:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        date_pt = date_obj.strftime('%d/%m/%Y')
        weekday = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'][date_obj.weekday()]
        
        cursor.execute('''
            SELECT r.*, u.shop_name 
            FROM requests r
            JOIN users u ON r.shop_telegram_id = u.telegram_id
            WHERE r.start_date = ? AND r.status = 'Aprovado'
            ORDER BY r.period
        ''', (date_str,))
        
        requests = cursor.fetchall()
        
        text += f"**{weekday}, {date_pt}**\n"
        
        if requests:
            for req in requests:
                period_emoji = "🌅" if req['period'] == "Manhã" else ("🌆" if req['period'] == "Tarde" else "📆")
                text += f"{period_emoji} {req['shop_name']} - {req['request_type']} ({req['period']})\n"
        else:
            text += "🟢 Sem pedidos aprovados\n"
        
        text += "\n"
    
    conn.close()
    
    await update.message.reply_text(text, parse_mode='Markdown')


async def lojas_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /lojas - Listar todas as lojas registadas (admin)"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Você não tem permissão para usar este comando.")
        return
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Obter todas as lojas
    cursor.execute('''
        SELECT 
            telegram_id,
            username,
            shop_name,
            is_admin,
            registered_at,
            (
                SELECT COUNT(*) 
                FROM requests 
                WHERE shop_telegram_id = users.telegram_id
            ) as total_pedidos
        FROM users
        ORDER BY shop_name ASC
    ''')
    
    lojas = cursor.fetchall()
    conn.close()
    
    if not lojas:
        await update.message.reply_text("📊 Nenhuma loja registada ainda.")
        return
    
    text = f"🏬 **Lista de Lojas Registadas** ({len(lojas)})\n\n"
    
    for loja in lojas:
        telegram_id, username, shop_name, is_admin, registered_at, total_pedidos = loja
        
        # Formatar data
        if registered_at:
            date_obj = datetime.strptime(registered_at, '%Y-%m-%d %H:%M:%S')
            date_str = date_obj.strftime('%d/%m/%Y')
        else:
            date_str = 'N/A'
        
        # Ícone de admin
        admin_badge = " 👑" if is_admin else ""
        
        # Escapar caracteres especiais do Markdown
        safe_shop_name = (shop_name or 'Sem nome').replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`')
        safe_username = (username or 'N/A').replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`')
        
        text += f"🏬 **{safe_shop_name}**{admin_badge}\n"
        text += f"   👤 @{safe_username}\n"
        text += f"   📅 Registado: {date_str}\n"
        text += f"   📋 Pedidos: {total_pedidos}\n\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /menu - Voltar ao menu principal"""
    user_id = update.effective_user.id
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        await update.message.reply_text(
            "👋 Bem-vindo! Use /start para se registar."
        )
        return
    
    if user_id in ADMIN_IDS:
        text = (
            f"👨‍💼 **Menu Administrador**\n\n"
            f"**Comandos disponíveis:**\n"
            f"• /pendentes - Ver pedidos pendentes\n"
            f"• /agenda_semana - Ver agenda da semana\n"
            f"• /estatisticas - Ver estatísticas\n"
            f"• /lojas - Ver lojas registadas\n"
            f"• /calendario - Ver calendário\n"
        )
    else:
        text = (
            f"🏬 **Menu Principal**\n\n"
            f"🏷️ Loja: {user['shop_name']}\n\n"
            f"**Comandos disponíveis:**\n"
            f"• /pedido - Criar novo pedido\n"
            f"• /calendario - Ver calendário\n"
            f"• /meus_pedidos - Ver meus pedidos\n"
            f"• /minha_loja - Informações da loja\n"
        )
    
    await update.message.reply_text(text, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help - Mostrar ajuda"""
    text = (
        "🔍 **Ajuda - Volante Minho 2.0**\n\n"
        "📝 **Como criar um pedido:**\n"
        "1. Use /pedido\n"
        "2. Escolha o tipo (Apoio, Férias, Outros)\n"
        "3. Selecione a data no calendário\n"
        "4. Escolha o período (Manhã, Tarde, Todo o dia)\n"
        "5. Adicione observações (opcional)\n\n"
        "📅 **Calendário:**\n"
        "🟢 Verde = Disponível\n"
        "🔴 Vermelho = Ocupado todo o dia\n"
        "🟣 Roxo = Manhã ocupada\n"
        "🔵 Azul = Tarde ocupada\n"
        "🟡 Amarelo = Pedido pendente\n\n"
        "🏖️ **Férias:**\n"
        "Para pedidos de férias, selecione a data de início e fim.\n"
        "O sistema criará automaticamente um pedido para cada dia.\n\n"
        "❓ **Dúvidas?**\n"
        "Entre em contacto com o gestor."
    )
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def setup_bot_commands(app: Application):
    """Configurar comandos do bot"""
    commands = [
        BotCommand("start", "Iniciar o bot"),
        BotCommand("pedido", "Criar novo pedido"),
        BotCommand("calendario", "Ver calendário de pedidos"),
        BotCommand("meus_pedidos", "Ver meus pedidos"),
        BotCommand("minha_loja", "Ver informações da minha loja"),
        BotCommand("pendentes", "Ver pedidos pendentes (admin)"),
        BotCommand("agenda_semana", "Ver agenda da semana (admin)"),
        BotCommand("estatisticas", "Ver estatísticas (admin)"),
        BotCommand("lojas", "Ver lojas registadas (admin)"),
        BotCommand("criar_pedido_admin", "Criar pedido pré-aprovado (admin)"),
        BotCommand("bloquear_dia", "Bloquear dias (admin)"),
        BotCommand("desbloquear_dia", "Desbloquear dias (admin)"),
        BotCommand("gerir_pedidos", "Gerir pedidos aprovados (admin)"),
        BotCommand("exportar_estatisticas", "Exportar estatísticas Excel (admin)"),
        BotCommand("menu", "Voltar ao menu principal"),
        BotCommand("help", "Mostrar ajuda"),
    ]
    
    await app.bot.set_my_commands(commands)
    logger.info("✅ Comandos configurados no menu do Telegram")


def main():
    """Iniciar o bot"""
    logger.info("🤖 Bot Volante Minho 2.0 V2 iniciado!")
    
    app = Application.builder().token(BOT_TOKEN).post_init(setup_bot_commands).build()
    
    # Configurar lembretes automáticos
    setup_reminders(app)
    
    # Configurar sincronização automática do dashboard
    setup_dashboard_sync(app)
    logger.info("✅ Sistema de lembretes configurado")
    
    # ConversationHandler para registo
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            AWAITING_SHOP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_shop_name)]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    app.add_handler(conv_handler)
    # Comando admin usa o mesmo fluxo do /pedido
    app.add_handler(CommandHandler('criar_pedido_admin', admin_create_request_start))
    app.add_handler(CommandHandler('pedido', pedido))
    app.add_handler(CommandHandler('calendario', calendario_command))
    app.add_handler(CommandHandler('meus_pedidos', meus_pedidos_command))
    app.add_handler(CommandHandler('minha_loja', minha_loja_command))
    app.add_handler(CommandHandler('pendentes', pendentes_command))
    app.add_handler(CommandHandler('estatisticas', estatisticas_command))
    app.add_handler(CommandHandler('agenda_semana', agenda_semana_command))
    app.add_handler(CommandHandler('lojas', lojas_command))
    app.add_handler(CommandHandler('bloquear_dia', bloquear_dia_command))
    app.add_handler(CommandHandler('desbloquear_dia', desbloquear_dia_command))
    app.add_handler(CommandHandler('gerir_pedidos', gerir_pedidos_command))
    app.add_handler(CommandHandler('exportar_estatisticas', exportar_estatisticas_command))
    app.add_handler(CommandHandler('menu', menu_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    # Iniciar polling
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
