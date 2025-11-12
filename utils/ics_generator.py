# -*- coding: utf-8 -*-
"""
Gerador de ficheiros .ics para eventos de calendário
"""

from datetime import datetime, timedelta
from ics import Calendar, Event
from config import CALENDAR_PERIODS


class ICSGenerator:
    """Gerador de ficheiros de calendário .ics"""
    
    @staticmethod
    def create_event(shop_name: str, request_type: str, date: str, period: str) -> str:
        """
        Cria um evento de calendário
        
        Args:
            shop_name: Nome da loja
            request_type: Tipo de pedido
            date: Data do evento (YYYY-MM-DD)
            period: Período do dia
            
        Returns:
            Conteúdo do ficheiro .ics como string
        """
        # Criar calendário
        cal = Calendar()
        
        # Criar evento
        event = Event()
        event.name = f"{request_type} - {shop_name}"
        
        # Obter horários do período
        period_times = CALENDAR_PERIODS.get(period, CALENDAR_PERIODS['Todo o dia'])
        
        # Parsear data
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        
        # Definir início e fim
        start_time = datetime.strptime(period_times['start'], '%H:%M:%S').time()
        end_time = datetime.strptime(period_times['end'], '%H:%M:%S').time()
        
        event.begin = datetime.combine(date_obj, start_time)
        event.end = datetime.combine(date_obj, end_time)
        
        # Adicionar descrição
        event.description = f"Tipo: {request_type}\nLoja: {shop_name}\nPeríodo: {period}"
        event.location = shop_name
        
        # Adicionar evento ao calendário
        cal.events.add(event)
        
        # Retornar conteúdo serializado
        return cal.serialize()
    
    @staticmethod
    def save_event_to_file(shop_name: str, request_type: str, date: str, period: str, filename: str) -> bool:
        """
        Salva um evento num ficheiro .ics
        
        Args:
            shop_name: Nome da loja
            request_type: Tipo de pedido
            date: Data do evento
            period: Período do dia
            filename: Nome do ficheiro de saída
            
        Returns:
            True se guardado com sucesso
        """
        try:
            ics_content = ICSGenerator.create_event(shop_name, request_type, date, period)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(ics_content)
            return True
        except Exception as e:
            print(f"Erro ao guardar ficheiro .ics: {e}")
            return False
    
    @staticmethod
    def create_google_calendar_link(shop_name: str, request_type: str, date: str, period: str) -> str:
        """
        Cria um link direto para adicionar ao Google Calendar
        
        Args:
            shop_name: Nome da loja
            request_type: Tipo de pedido
            date: Data do evento
            period: Período do dia
            
        Returns:
            URL do Google Calendar
        """
        from urllib.parse import quote
        
        # Obter horários
        period_times = CALENDAR_PERIODS.get(period, CALENDAR_PERIODS['Todo o dia'])
        
        # Parsear data
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        start_time = datetime.strptime(period_times['start'], '%H:%M:%S').time()
        end_time = datetime.strptime(period_times['end'], '%H:%M:%S').time()
        
        start_dt = datetime.combine(date_obj, start_time)
        end_dt = datetime.combine(date_obj, end_time)
        
        # Formato para Google Calendar: YYYYMMDDTHHmmSS
        start_str = start_dt.strftime('%Y%m%dT%H%M%S')
        end_str = end_dt.strftime('%Y%m%dT%H%M%S')
        
        title = quote(f"{request_type} - {shop_name}")
        details = quote(f"Tipo: {request_type}\nLoja: {shop_name}\nPeríodo: {period}")
        location = quote(shop_name)
        
        url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={title}&dates={start_str}/{end_str}&details={details}&location={location}"
        
        return url
