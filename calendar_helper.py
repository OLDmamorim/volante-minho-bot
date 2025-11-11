# -*- coding: utf-8 -*-
"""
Utilitários de Calendário Inline para Telegram
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
import calendar


class TelegramCalendar:
    """Calendário inline para seleção de datas no Telegram"""
    
    def __init__(self, year: int = None, month: int = None):
        """
        Inicializa o calendário
        
        Args:
            year: Ano (padrão: ano atual)
            month: Mês (padrão: mês atual)
        """
        now = datetime.now()
        self.year = year or now.year
        self.month = month or now.month
    
    def create_calendar(self) -> InlineKeyboardMarkup:
        """
        Cria o teclado inline do calendário
        
        Returns:
            InlineKeyboardMarkup com o calendário
        """
        keyboard = []
        
        # Cabeçalho com mês e ano
        month_name = calendar.month_name[self.month]
        header = [InlineKeyboardButton(
            f"{month_name} {self.year}",
            callback_data="calendar_ignore"
        )]
        keyboard.append(header)
        
        # Dias da semana
        week_days = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        keyboard.append([
            InlineKeyboardButton(day, callback_data="calendar_ignore")
            for day in week_days
        ])
        
        # Dias do mês
        month_calendar = calendar.monthcalendar(self.year, self.month)
        for week in month_calendar:
            row = []
            for day in week:
                if day == 0:
                    # Dia vazio
                    row.append(InlineKeyboardButton(" ", callback_data="calendar_ignore"))
                else:
                    # Verificar se é dia passado
                    date = datetime(self.year, self.month, day)
                    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    
                    if date < today:
                        # Dia passado - desabilitado
                        row.append(InlineKeyboardButton(
                            f"·{day}·",
                            callback_data="calendar_ignore"
                        ))
                    else:
                        # Dia selecionável
                        row.append(InlineKeyboardButton(
                            str(day),
                            callback_data=f"calendar_day_{self.year}_{self.month}_{day}"
                        ))
            keyboard.append(row)
        
        # Navegação entre meses
        navigation = []
        
        # Botão mês anterior
        prev_month = self.month - 1
        prev_year = self.year
        if prev_month < 1:
            prev_month = 12
            prev_year -= 1
        
        # Só mostrar mês anterior se não for no passado
        if prev_year > datetime.now().year or (prev_year == datetime.now().year and prev_month >= datetime.now().month):
            navigation.append(InlineKeyboardButton(
                "◀️",
                callback_data=f"calendar_prev_{prev_year}_{prev_month}"
            ))
        else:
            navigation.append(InlineKeyboardButton(" ", callback_data="calendar_ignore"))
        
        # Botão mês seguinte
        next_month = self.month + 1
        next_year = self.year
        if next_month > 12:
            next_month = 1
            next_year += 1
        
        navigation.append(InlineKeyboardButton(
            "▶️",
            callback_data=f"calendar_next_{next_year}_{next_month}"
        ))
        
        keyboard.append(navigation)
        
        # Botão cancelar
        keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="calendar_cancel")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def process_selection(data: str) -> tuple:
        """
        Processa a seleção de uma data
        
        Args:
            data: Callback data do botão
            
        Returns:
            Tupla (action, year, month, day) ou (action, year, month) ou (action,)
        """
        parts = data.split('_')
        
        if parts[0] != 'calendar':
            return (None,)
        
        action = parts[1]
        
        if action == 'day':
            return ('day', int(parts[2]), int(parts[3]), int(parts[4]))
        elif action in ['prev', 'next']:
            return (action, int(parts[2]), int(parts[3]))
        elif action in ['ignore', 'cancel']:
            return (action,)
        
        return (None,)
    
    @staticmethod
    def format_date(year: int, month: int, day: int) -> str:
        """
        Formata uma data
        
        Args:
            year: Ano
            month: Mês
            day: Dia
            
        Returns:
            Data formatada (YYYY-MM-DD)
        """
        return f"{year:04d}-{month:02d}-{day:02d}"
    
    @staticmethod
    def format_date_pt(year: int, month: int, day: int) -> str:
        """
        Formata uma data em português
        
        Args:
            year: Ano
            month: Mês
            day: Dia
            
        Returns:
            Data formatada (DD/MM/YYYY)
        """
        return f"{day:02d}/{month:02d}/{year:04d}"
