# -*- coding: utf-8 -*-
"""
Geração de Links para Calendários (Google Calendar e iOS Calendar)
"""
from datetime import datetime, timedelta
from urllib.parse import quote


def generate_calendar_links(request_data):
    """
    Gera links para Google Calendar e iOS Calendar
    
    Args:
        request_data: dict com 'shop_name', 'request_type', 'start_date', 'period', 'observations'
    
    Returns:
        tuple: (google_calendar_url, ios_calendar_data)
    """
    shop_name = request_data.get('shop_name', 'Loja')
    request_type = request_data.get('request_type', 'Apoio')
    date_str = request_data.get('start_date')  # formato: YYYY-MM-DD
    period = request_data.get('period', 'Todo o dia')
    observations = request_data.get('observations', '')
    
    # Converter data
    date = datetime.strptime(date_str, '%Y-%m-%d')
    
    # Definir horários baseado no período
    if period == 'Manhã':
        start_time = date.replace(hour=9, minute=0, second=0)
        end_time = date.replace(hour=13, minute=0, second=0)
    elif period == 'Tarde':
        start_time = date.replace(hour=14, minute=0, second=0)
        end_time = date.replace(hour=18, minute=0, second=0)
    else:  # Todo o dia
        start_time = date.replace(hour=0, minute=0, second=0)
        end_time = date.replace(hour=23, minute=59, second=59)
    
    # Título e descrição
    title = f"{request_type} - {shop_name} ({period})"
    description = f"Tipo: {request_type}\nLoja: {shop_name}\nPeríodo: {period}"
    
    if observations:
        description += f"\\nObservações: {observations}"
    
    # Google Calendar URL
    google_start = start_time.strftime('%Y%m%dT%H%M%S')
    google_end = end_time.strftime('%Y%m%dT%H%M%S')
    
    google_url = (
        f"https://calendar.google.com/calendar/render?"
        f"action=TEMPLATE&"
        f"text={quote(title)}&"
        f"dates={google_start}/{google_end}&"
        f"details={quote(description)}&"
        f"sf=true&"
        f"output=xml"
    )
    
    # iOS Calendar (formato .ics)
    ics_start = start_time.strftime('%Y%m%dT%H%M%S')
    ics_end = end_time.strftime('%Y%m%dT%H%M%S')
    
    # Preparar descrição para ICS
    ics_description = description.replace('\n', '\\n')
    
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Volante Minho//PT
BEGIN:VEVENT
UID:{date_str}-{shop_name}@volanteminho.pt
DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{ics_start}
DTEND:{ics_end}
SUMMARY:{title}
DESCRIPTION:{ics_description}
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""
    
    return google_url, ics_content


def create_calendar_buttons(google_url):
    """
    Cria botões inline para adicionar ao calendário
    
    Returns:
        InlineKeyboardMarkup
    """
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [InlineKeyboardButton("📅 Adicionar ao Google Calendar", url=google_url)],
    ]
    
    return InlineKeyboardMarkup(keyboard)
