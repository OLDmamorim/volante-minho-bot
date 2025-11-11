# -*- coding: utf-8 -*-
"""
Calendário Visual com Cores para Status de Pedidos
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
import calendar as cal_module
import sqlite3

DB_PATH = "database/hugo_bot.db"


def get_day_status(year, month, day):
    """
    Retorna o status de um dia baseado nos pedidos
    
    Returns:
        str: 'disponivel', 'ocupado_dia', 'ocupado_manha', 'ocupado_tarde', 'pendente'
    """
    date_str = f"{year:04d}-{month:02d}-{day:02d}"
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Buscar pedidos para este dia
    cursor.execute('''
        SELECT status, period FROM requests 
        WHERE start_date = ?
    ''', (date_str,))
    requests = cursor.fetchall()
    conn.close()
    
    if not requests:
        return 'disponivel'
    
    # Verificar se há pendentes
    has_pendente = any(r['status'] == 'Pendente' for r in requests)
    if has_pendente:
        return 'pendente'
    
    # Verificar ocupação
    aprovados = [r for r in requests if r['status'] == 'Aprovado']
    
    if not aprovados:
        return 'disponivel'
    
    # Verificar períodos
    periodos = [r['period'] for r in aprovados]
    
    if 'Todo o dia' in periodos:
        return 'ocupado_dia'
    
    if 'Manhã' in periodos and 'Tarde' in periodos:
        return 'ocupado_dia'
    
    if 'Manhã' in periodos:
        return 'ocupado_manha'
    
    if 'Tarde' in periodos:
        return 'ocupado_tarde'
    
    return 'disponivel'


def create_visual_calendar(year=None, month=None):
    """
    Cria calendário visual com cores
    
    Returns:
        InlineKeyboardMarkup
    """
    now = datetime.now()
    year = year or now.year
    month = month or now.month
    
    keyboard = []
    
    # Cabeçalho
    month_name = ['', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
                  'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'][month]
    header = [InlineKeyboardButton(
        f"📅 {month_name} {year}",
        callback_data="cal_ignore"
    )]
    keyboard.append(header)
    
    # Dias da semana
    week_days = ["D", "S", "T", "Q", "Q", "S", "S"]
    keyboard.append([
        InlineKeyboardButton(day, callback_data="cal_ignore")
        for day in week_days
    ])
    
    # Dias do mês
    month_calendar = cal_module.monthcalendar(year, month)
    
    for week in month_calendar:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data="cal_ignore"))
            else:
                # Verificar se é dia passado
                date = datetime(year, month, day)
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                
                if date < today:
                    row.append(InlineKeyboardButton(
                        f"·{day}·",
                        callback_data="cal_ignore"
                    ))
                else:
                    # Obter status do dia
                    status = get_day_status(year, month, day)
                    
                    # Emoji baseado no status
                    emoji = {
                        'disponivel': '🟢',
                        'ocupado_dia': '🔴',
                        'ocupado_manha': '🟣',
                        'ocupado_tarde': '🔵',
                        'pendente': '🟡'
                    }.get(status, '🟢')
                    
                    row.append(InlineKeyboardButton(
                        f"{day}{emoji}",
                        callback_data=f"cal_day_{year}_{month}_{day}"
                    ))
        
        keyboard.append(row)
    
    # Navegação
    navigation = []
    
    prev_month = month - 1
    prev_year = year
    if prev_month < 1:
        prev_month = 12
        prev_year -= 1
    
    if prev_year > now.year or (prev_year == now.year and prev_month >= now.month):
        navigation.append(InlineKeyboardButton(
            "◀️",
            callback_data=f"cal_prev_{prev_year}_{prev_month}"
        ))
    else:
        navigation.append(InlineKeyboardButton(" ", callback_data="cal_ignore"))
    
    next_month = month + 1
    next_year = year
    if next_month > 12:
        next_month = 1
        next_year += 1
    
    navigation.append(InlineKeyboardButton(
        "▶️",
        callback_data=f"cal_next_{next_year}_{next_month}"
    ))
    
    keyboard.append(navigation)
    
    # Legenda
    keyboard.append([InlineKeyboardButton(
        "🟢 Disponível | 🔴 Ocupado | 🟣 Manhã | 🔵 Tarde | 🟡 Pendente",
        callback_data="cal_ignore"
    )])
    
    # Fechar
    keyboard.append([InlineKeyboardButton("❌ Fechar", callback_data="cal_close")])
    
    return InlineKeyboardMarkup(keyboard)


def process_calendar_callback(data):
    """
    Processa callback do calendário
    
    Returns:
        tuple: (action, year, month, day) ou (action, year, month) ou (action,)
    """
    parts = data.split('_')
    
    if parts[0] != 'cal':
        return (None,)
    
    action = parts[1]
    
    if action == 'day':
        return ('day', int(parts[2]), int(parts[3]), int(parts[4]))
    elif action in ['prev', 'next']:
        return (action, int(parts[2]), int(parts[3]))
    elif action in ['ignore', 'close']:
        return (action,)
    
    return (None,)
