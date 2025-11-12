# -*- coding: utf-8 -*-
"""
Sistema de Lembretes Automáticos para Gestores
"""
import logging
import sqlite3
from datetime import datetime, time
from telegram import Bot
from telegram.ext import Application
import asyncio

logger = logging.getLogger(__name__)

DB_PATH = "database/hugo_bot.db"


def get_pending_requests():
    """Obter pedidos pendentes"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                r.id,
                u.shop_name,
                r.request_type,
                r.start_date,
                r.period,
                r.created_at
            FROM requests r
            LEFT JOIN users u ON r.shop_telegram_id = u.telegram_id
            WHERE r.status = 'Pendente'
            ORDER BY r.created_at ASC
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    except Exception as e:
        logger.error(f"Erro ao obter pedidos pendentes: {e}")
        return []


def get_today_schedule():
    """Obter planeamento do dia atual"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Pedidos aprovados para hoje
        cursor.execute("""
            SELECT 
                u.shop_name,
                r.request_type,
                r.period,
                r.start_date,
                r.end_date
            FROM requests r
            LEFT JOIN users u ON r.shop_telegram_id = u.telegram_id
            WHERE r.status = 'Aprovado'
            AND (
                r.start_date = ?
                OR (r.start_date <= ? AND r.end_date >= ?)
            )
            ORDER BY r.period ASC
        """, (today, today, today))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    except Exception as e:
        logger.error(f"Erro ao obter planeamento do dia: {e}")
        return []


def get_admin_users():
    """Obter lista de administradores"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT telegram_id, username
            FROM users
            WHERE is_admin = 1
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    except Exception as e:
        logger.error(f"Erro ao obter administradores: {e}")
        return []


async def send_pending_reminder(application: Application):
    """Enviar lembrete de pedidos pendentes"""
    try:
        pending = get_pending_requests()
        
        if not pending:
            logger.info("Nenhum pedido pendente para lembrar")
            return
        
        admins = get_admin_users()
        
        if not admins:
            logger.warning("Nenhum administrador encontrado")
            return
        
        # Construir mensagem
        message = "🔔 **Lembrete de Pedidos Pendentes**\n\n"
        message += f"Existem **{len(pending)}** pedido(s) pendente(s) de aprovação:\n\n"
        
        for req in pending[:5]:  # Mostrar no máximo 5
            req_id, shop_name, req_type, start_date, period, created_at = req
            
            # Calcular tempo de espera
            created = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
            wait_hours = int((datetime.now() - created).total_seconds() / 3600)
            
            message += f"📋 **{shop_name or 'Loja'}** - {req_type}\n"
            message += f"   📅 {start_date} ({period or 'Todo o dia'})\n"
            message += f"   ⏰ Aguarda há {wait_hours}h\n\n"
        
        if len(pending) > 5:
            message += f"... e mais {len(pending) - 5} pedido(s)\n\n"
        
        message += "Use /pendentes para ver todos os detalhes."
        
        # Enviar para todos os admins
        for admin_id, admin_name in admins:
            try:
                await application.bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode='Markdown'
                )
                logger.info(f"Lembrete de pendentes enviado para {admin_name}")
            except Exception as e:
                logger.error(f"Erro ao enviar lembrete para {admin_name}: {e}")
        
    except Exception as e:
        logger.error(f"Erro ao enviar lembrete de pendentes: {e}")


async def send_daily_schedule(application: Application):
    """Enviar resumo diário de planeamento"""
    try:
        schedule = get_today_schedule()
        admins = get_admin_users()
        
        if not admins:
            logger.warning("Nenhum administrador encontrado")
            return
        
        # Construir mensagem
        today_str = datetime.now().strftime('%d/%m/%Y')
        weekday = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'][datetime.now().weekday()]
        
        message = f"☀️ **Bom dia! Planeamento de {weekday}, {today_str}**\n\n"
        
        if not schedule:
            message += "✅ Nenhum pedido agendado para hoje.\n"
            message += "Todos os colaboradores disponíveis! 🎉"
        else:
            # Organizar por período
            manha = [s for s in schedule if s[2] and 'Manhã' in s[2]]
            tarde = [s for s in schedule if s[2] and 'Tarde' in s[2]]
            todo_dia = [s for s in schedule if s[2] and 'Todo o dia' in s[2]]
            
            if manha:
                message += "🌅 **Manhã:**\n"
                for shop, req_type, period, start, end in manha:
                    message += f"   • {shop or 'Loja'} - {req_type}\n"
                message += "\n"
            
            if tarde:
                message += "🌆 **Tarde:**\n"
                for shop, req_type, period, start, end in tarde:
                    message += f"   • {shop or 'Loja'} - {req_type}\n"
                message += "\n"
            
            if todo_dia:
                message += "📅 **Todo o dia:**\n"
                for shop, req_type, period, start, end in todo_dia:
                    if end and end != start:
                        message += f"   • {shop or 'Loja'} - {req_type} (até {end})\n"
                    else:
                        message += f"   • {shop or 'Loja'} - {req_type}\n"
                message += "\n"
            
            pass  # Total removido conforme solicitado
        
        # Adicionar info de pedidos pendentes
        pending = get_pending_requests()
        if pending:
            message += f"\n\n⚠️ **{len(pending)}** pedido(s) pendente(s) de aprovação"
            message += "\nUse /pendentes para revisar."
        
        # Enviar para todos os admins
        for admin_id, admin_name in admins:
            try:
                await application.bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode='Markdown'
                )
                logger.info(f"Resumo diário enviado para {admin_name}")
            except Exception as e:
                logger.error(f"Erro ao enviar resumo para {admin_name}: {e}")
        
    except Exception as e:
        logger.error(f"Erro ao enviar resumo diário: {e}")


async def check_urgent_requests(application: Application):
    """Verificar pedidos urgentes (mais de 24h pendentes)"""
    try:
        pending = get_pending_requests()
        urgent = []
        
        for req in pending:
            req_id, shop_name, req_type, start_date, period, created_at = req
            created = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
            wait_hours = (datetime.now() - created).total_seconds() / 3600
            
            if wait_hours >= 24:
                urgent.append((shop_name, req_type, start_date, int(wait_hours)))
        
        if not urgent:
            return
        
        admins = get_admin_users()
        
        message = "🚨 **ALERTA: Pedidos Urgentes**\n\n"
        message += f"Os seguintes pedidos estão pendentes há mais de 24 horas:\n\n"
        
        for shop, req_type, start_date, hours in urgent:
            message += f"⚠️ **{shop or 'Loja'}** - {req_type}\n"
            message += f"   📅 {start_date}\n"
            message += f"   ⏰ Aguarda há **{hours}h**\n\n"
        
        message += "Por favor, revise estes pedidos o mais rápido possível.\n"
        message += "Use /pendentes para aprovar ou rejeitar."
        
        # Enviar para todos os admins
        for admin_id, admin_name in admins:
            try:
                await application.bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode='Markdown'
                )
                logger.info(f"Alerta de urgentes enviado para {admin_name}")
            except Exception as e:
                logger.error(f"Erro ao enviar alerta para {admin_name}: {e}")
        
    except Exception as e:
        logger.error(f"Erro ao verificar pedidos urgentes: {e}")


def setup_reminders(application: Application):
    """Configurar jobs de lembretes"""
    job_queue = application.job_queue
    
    # Resumo diário às 8:30 (apenas dias úteis - segunda a sexta)
    job_queue.run_daily(
        send_daily_schedule,
        time=time(hour=8, minute=30),
        days=(0, 1, 2, 3, 4),  # 0=segunda, 1=terça, 2=quarta, 3=quinta, 4=sexta
        name='daily_schedule'
    )
    logger.info("✅ Lembrete diário configurado para 8:30 (dias úteis)")
    
    # Lembrete de pendentes a cada 4 horas (9:00, 13:00, 17:00)
    for hour in [9, 13, 17]:
        job_queue.run_daily(
            send_pending_reminder,
            time=time(hour=hour, minute=0),
            name=f'pending_reminder_{hour}'
        )
    logger.info("✅ Lembretes de pendentes configurados (9h, 13h, 17h)")
    
    # Verificar urgentes a cada 6 horas
    job_queue.run_repeating(
        check_urgent_requests,
        interval=21600,  # 6 horas em segundos
        first=10,  # Começar após 10 segundos
        name='urgent_check'
    )
    logger.info("✅ Verificação de urgentes configurada (a cada 6h)")
