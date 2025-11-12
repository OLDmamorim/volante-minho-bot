#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Volante Minho 2.0 - Bot do Telegram COMPLETO
Todas as funcionalidades implementadas
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
    ConversationHandler,
    filters,
)
from calendar_helper import TelegramCalendar
from visual_calendar import create_visual_calendar, process_calendar_callback, get_day_status
from calendar_links import generate_calendar_links, create_calendar_buttons

# Configuração
BOT_TOKEN = "8365753572:AAGiZrUoYxxfYlrRWZaIwNGkKiWQ_EzdX78"
ADMIN_IDS = [228613920, 615966323]
DB_PATH = "database/hugo_bot.db"

# Estados da conversação
AWAITING_SHOP_NAME, AWAITING_OBSERVATIONS = range(2)

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
        
        if not is_admin:
            conn.close()
            await update.message.reply_text("👋 Bem-vindo! Por favor, indique o nome da sua loja:")
            return AWAITING_SHOP_NAME
    
    conn.close()
    
    if is_admin:
        welcome_text = f"""
👋 Bem-vindo de volta, Administrador!

**Comandos disponíveis:**

/pendentes - Ver pedidos pendentes
/agenda_semana - Ver agenda da semana  
/calendario - Ver calendário de pedidos
/estatisticas - Ver estatísticas completas
/listar_usuarios - Listar todos os utilizadores
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
            return AWAITING_SHOP_NAME
        
        shop_name = user_data['shop_name']
        
        welcome_text = f"""
👋 Bem-vindo de volta!
🏬 Loja: {shop_name}
🆔 ID: {user_id}

**Comandos disponíveis:**

/pedido - Criar novo pedido
/calendario - Ver calendário de pedidos
/meus_pedidos - Ver meus pedidos
/minha_loja - Ver informações da minha loja
"""
    
    # Botão Menu persistente
    keyboard = [[KeyboardButton("≡ Menu")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    return ConversationHandler.END


async def receive_shop_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe o nome da loja"""
    user_id = update.effective_user.id
    shop_name = update.message.text.strip()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET shop_name = ? WHERE telegram_id = ?', (shop_name, user_id))
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
        return
    
    # Tipo de pedido
    if data.startswith("tipo_"):
        tipo = data.replace("tipo_", "")
        context.user_data['request_type'] = tipo
        
        # Mostrar calendário
        cal = TelegramCalendar()
        await query.edit_message_text(
            f"📝 Tipo: **{tipo}**\n\nSelecione a data:",
            reply_markup=cal.create_calendar(),
            parse_mode='Markdown'
        )
        return
    
    # Calendário Visual
    if data.startswith("cal_"):
        result = process_calendar_callback(data)
        
        if result[0] == "day":
            _, year, month, day = result
            date_str = f"{day:02d}/{month:02d}/{year:04d}"
            status = get_day_status(year, month, day)
            
            status_text = {
                'disponivel': '🟢 Disponível',
                'ocupado_dia': '🔴 Ocupado (todo o dia)',
                'ocupado_manha': '🟣 Ocupado (manhã)',
                'ocupado_tarde': '🔵 Ocupado (tarde)',
                'pendente': '🟡 Pendente de aceitação'
            }.get(status, 'Desconhecido')
            
            await query.answer(f"{date_str}: {status_text}")
            return
            
        elif result[0] in ["prev", "next"]:
            _, year, month = result
            calendar_markup = create_visual_calendar(year, month)
            
            await query.edit_message_text(
                "📆 **Calendário de Pedidos**\n\n"
                "🟢 Disponível\n"
                "🔴 Ocupado (todo o dia)\n"
                "🟣 Ocupado (manhã)\n"
                "🔵 Ocupado (tarde)\n"
                "🟡 Pendente de aceitação",
                reply_markup=calendar_markup,
                parse_mode='Markdown'
            )
            return
            
        elif result[0] == "close":
            await query.edit_message_text("✅ Calendário fechado.")
            return
    
    # Calendário de Pedidos
    if data.startswith("calendar_"):
        result = TelegramCalendar.process_selection(data)
        
        if result[0] == "day":
            # Data selecionada
            _, year, month, day = result
            date_str = TelegramCalendar.format_date(year, month, day)
            date_pt = TelegramCalendar.format_date_pt(year, month, day)
            
            context.user_data['date'] = date_str
            context.user_data['date_pt'] = date_pt
            
            # Mostrar períodos
            keyboard = [
                [InlineKeyboardButton("🌅 Manhã", callback_data="periodo_Manhã")],
                [InlineKeyboardButton("🌆 Tarde", callback_data="periodo_Tarde")],
                [InlineKeyboardButton("📆 Todo o dia", callback_data="periodo_Todo o dia")],
                [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"📝 Tipo: **{context.user_data.get('request_type')}**\n"
                f"📅 Data: **{date_pt}**\n\n"
                f"Selecione o período:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        elif result[0] in ["prev", "next"]:
            # Navegar mês
            _, year, month = result
            cal = TelegramCalendar(year, month)
            await query.edit_message_text(
                f"📝 Tipo: **{context.user_data.get('request_type')}**\n\nSelecione a data:",
                reply_markup=cal.create_calendar(),
                parse_mode='Markdown'
            )
            
        elif result[0] == "cancel":
            await query.edit_message_text("❌ Operação cancelada.")
        
        return
    
    # Período
    if data.startswith("periodo_"):
        periodo = data.replace("periodo_", "")
        context.user_data['period'] = periodo
        
        # Pedir observações
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
        return
    
    # Rejeitar pedido
    if data.startswith("rejeitar_"):
        request_id = int(data.replace("rejeitar_", ""))
        context.user_data['rejecting_request_id'] = request_id
        
        await query.edit_message_text(
            "❌ **Rejeitar Pedido**\n\n"
            "Por favor, indique o motivo da rejeição:",
            parse_mode='Markdown'
        )
        return


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para mensagens de texto"""
    text = update.message.text.strip()
    
    # Observações do pedido
    if context.user_data.get('awaiting_observations'):
        context.user_data['awaiting_observations'] = False
        
        observations = None if text.lower() == "não" else text
        
        # Criar pedido
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO requests (
                shop_telegram_id, request_type, start_date, period, status
            ) VALUES (?, ?, ?, ?, 'Pendente')
        ''', (
            update.effective_user.id,
            context.user_data.get('request_type'),
            context.user_data.get('date'),
            context.user_data.get('period')
        ))
        
        request_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Confirmar
        await update.message.reply_text(
            f"✅ **Pedido criado com sucesso!**\n\n"
            f"📝 Tipo: {context.user_data.get('request_type')}\n"
            f"📅 Data: {context.user_data.get('date_pt')}\n"
            f"🕐 Período: {context.user_data.get('period')}\n"
            f"{'📝 Obs: ' + observations if observations else ''}",
            parse_mode='Markdown'
        )
        
        # Notificar admins
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT shop_name FROM users WHERE telegram_id = ?', (update.effective_user.id,))
        user_data = cursor.fetchone()
        conn.close()
        
        for admin_id in ADMIN_IDS:
            try:
                keyboard = [
                    [InlineKeyboardButton("✅ Aprovar", callback_data=f"aprovar_{request_id}")],
                    [InlineKeyboardButton("❌ Rejeitar", callback_data=f"rejeitar_{request_id}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"🔔 **Novo Pedido #{request_id}**\n\n"
                         f"🏬 Loja: {user_data['shop_name']}\n"
                         f"📝 Tipo: {context.user_data.get('request_type')}\n"
                         f"📅 Data: {context.user_data.get('date_pt')}\n"
                         f"🕐 Período: {context.user_data.get('period')}\n"
                         f"{'📝 Obs: ' + observations if observations else ''}",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            except:
                pass
        
        # Limpar contexto
        context.user_data.clear()
        return
    
    # Motivo de rejeição
    if 'rejecting_request_id' in context.user_data:
        request_id = context.user_data['rejecting_request_id']
        reason = text
        admin_id = update.effective_user.id
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Atualizar pedido
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
            f"❌ **Pedido #{request_id} Rejeitado**\n\n"
            f"🏬 Loja: {req['shop_name']}\n"
            f"**Motivo:** {reason}",
            parse_mode='Markdown'
        )
        
        del context.user_data['rejecting_request_id']
        return


async def meus_pedidos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /meus_pedidos"""
    user_id = update.effective_user.id
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM requests 
        WHERE shop_telegram_id = ? 
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
        message += f"📅 {req['start_date']} ({req['period']})\n"
        
        if req['status'] == 'Rejeitado' and req['rejection_reason']:
            message += f"💬 Motivo: {req['rejection_reason']}\n"
        
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
        JOIN users u ON r.shop_telegram_id = u.telegram_id
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
        keyboard = [
            [InlineKeyboardButton("✅ Aprovar", callback_data=f"aprovar_{req['id']}")],
            [InlineKeyboardButton("❌ Rejeitar", callback_data=f"rejeitar_{req['id']}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"🔔 **Pedido #{req['id']}**\n\n"
            f"🏬 Loja: {req['shop_name']}\n"
            f"📝 Tipo: {req['request_type']}\n"
            f"📅 Data: {req['start_date']}\n"
            f"🕐 Período: {req['period']}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


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
    
    # Por tipo
    cursor.execute('SELECT request_type, COUNT(*) as count FROM requests GROUP BY request_type')
    por_tipo = cursor.fetchall()
    
    # Por período
    cursor.execute('SELECT period, COUNT(*) as count FROM requests GROUP BY period')
    por_periodo = cursor.fetchall()
    
    # Por loja
    cursor.execute('''
        SELECT u.shop_name, COUNT(*) as count 
        FROM requests r
        JOIN users u ON r.shop_telegram_id = u.telegram_id
        GROUP BY u.shop_name
        ORDER BY count DESC
    ''')
    por_loja = cursor.fetchall()
    
    conn.close()
    
    # Processar status
    pendentes_count = sum(r['count'] for r in por_status if r['status'] == 'Pendente')
    aprovados = sum(r['count'] for r in por_status if r['status'] == 'Aprovado')
    rejeitados = sum(r['count'] for r in por_status if r['status'] == 'Rejeitado')
    
    message = f"""
📊 **ESTATÍSTICAS DE PEDIDOS**

📄 Total de pedidos: {total}

🟢 **Por Status:**
⏳ Pendentes: {pendentes_count}
✅ Aprovados: {aprovados}
❌ Rejeitados: {rejeitados}

🔧 **Por Tipo de Serviço:**
"""
    
    for tipo in por_tipo:
        emoji = {
            'Apoio': '🔧',
            'Férias': '🏖️',
            'Outros': '📋'
        }.get(tipo['request_type'], '📋')
        message += f"{emoji} {tipo['request_type']}: {tipo['count']}\n"
    
    message += "\n⏰ **Por Período:**\n"
    
    for periodo in por_periodo:
        emoji = {
            'Manhã': '🌅',
            'Tarde': '🌆',
            'Todo o dia': '📆'
        }.get(periodo['period'], '📆')
        message += f"{emoji} {periodo['period']}: {periodo['count']}\n"
    
    message += "\n🏬 **Por Loja:**\n"
    
    for loja in por_loja:
        message += f"{loja['shop_name']}: {loja['count']}\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def calendario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /calendario"""
    calendar_markup = create_visual_calendar()
    
    await update.message.reply_text(
        "📆 **Calendário de Pedidos**\n\n"
        "🟢 Disponível\n"
        "🔴 Ocupado (todo o dia)\n"
        "🟣 Ocupado (manhã)\n"
        "🔵 Ocupado (tarde)\n"
        "🟡 Pendente de aceitação",
        reply_markup=calendar_markup,
        parse_mode='Markdown'
    )


async def agenda_semana(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /agenda_semana"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Apenas administradores podem usar este comando.")
        return
    
    # Calcular datas
    hoje = datetime.now().date()
    proxima_semana = hoje + timedelta(days=7)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.*, u.shop_name 
        FROM requests r
        JOIN users u ON r.shop_telegram_id = u.telegram_id
        WHERE r.status = 'Aprovado' 
        AND date(r.start_date) BETWEEN date(?) AND date(?)
        ORDER BY r.start_date
    ''', (str(hoje), str(proxima_semana)))
    requests = cursor.fetchall()
    conn.close()
    
    if not requests:
        await update.message.reply_text("✅ Não há pedidos agendados para a próxima semana!")
        return
    
    message = f"📅 **Agenda da Semana ({len(requests)} pedidos)**\n\n"
    
    for req in requests:
        # Formatar data
        date_obj = datetime.strptime(req['start_date'], '%Y-%m-%d')
        date_str = date_obj.strftime('%d/%m/%Y')
        day_name = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'][date_obj.weekday()]
        
        # Emoji período
        periodo_emoji = {
            'Manhã': '🌅',
            'Tarde': '🌆',
            'Todo o dia': '📆'
        }.get(req['period'], '📆')
        
        message += f"{periodo_emoji} **{day_name} {date_str}**\n"
        message += f"🏬 {req['shop_name']} - {req['request_type']}\n\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')


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


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help"""
    await start(update, context)


async def menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para botão Menu"""
    await start(update, context)


async def setup_commands(application: Application):
    """Configurar comandos do bot"""
    commands = [
        BotCommand("start", "Iniciar o bot"),
        BotCommand("pedido", "Criar novo pedido"),
        BotCommand("calendario", "Ver calendário de pedidos"),
        BotCommand("meus_pedidos", "Ver meus pedidos"),
        BotCommand("minha_loja", "Ver informações da minha loja"),
        BotCommand("pendentes", "Ver pedidos pendentes"),
        BotCommand("agenda_semana", "Ver agenda da semana"),
        BotCommand("estatisticas", "Ver estatísticas completas"),
        BotCommand("listar_usuarios", "Listar todos os utilizadores"),
        BotCommand("help", "Mostrar ajuda")
    ]
    
    await application.bot.set_my_commands(commands)
    logger.info("✅ Comandos configurados no menu do Telegram")


def main():
    """Função principal"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # ConversationHandler para registo
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            AWAITING_SHOP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_shop_name)],
        },
        fallbacks=[CommandHandler('start', start)],
    )
    
    application.add_handler(conv_handler)
    
    # Comandos
    application.add_handler(CommandHandler("pedido", pedido))
    application.add_handler(CommandHandler("meus_pedidos", meus_pedidos))
    application.add_handler(CommandHandler("minha_loja", minha_loja))
    application.add_handler(CommandHandler("pendentes", pendentes))
    application.add_handler(CommandHandler("estatisticas", estatisticas))
    application.add_handler(CommandHandler("calendario", calendario))
    application.add_handler(CommandHandler("agenda_semana", agenda_semana))
    application.add_handler(CommandHandler("agendasemana", agenda_semana))
    application.add_handler(CommandHandler("listar_usuarios", listar_usuarios))
    application.add_handler(CommandHandler("listarusuarios", listar_usuarios))
    application.add_handler(CommandHandler("help", help_command))
    
    # Callbacks
    application.add_handler(CallbackQueryHandler(callback_handler))
    
    # Texto
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^≡ Menu$"), handle_text))
    
    # Botão Menu
    application.add_handler(MessageHandler(filters.Regex("^≡ Menu$"), menu_button))
    
    # Configurar comandos
    application.post_init = setup_commands
    
    logger.info("🤖 Bot Volante Minho 2.0 COMPLETO iniciado!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
