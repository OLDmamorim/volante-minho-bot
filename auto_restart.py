# -*- coding: utf-8 -*-
"""
Sistema de restart automático diário
"""
import logging
from datetime import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


async def daily_restart_notification():
    """Notificar que o restart diário vai acontecer"""
    logger.info("🔄 Restart automático diário agendado para daqui a 5 minutos...")
    # O Railway vai fazer restart automaticamente às 4h via config


def setup_auto_restart(app):
    """Configurar restart automático diário"""
    scheduler = AsyncIOScheduler()
    
    # Agendar notificação de restart para 3:55 AM (5 min antes do restart real)
    scheduler.add_job(
        daily_restart_notification,
        trigger=CronTrigger(hour=3, minute=55, timezone='UTC'),
        id='daily_restart_notification',
        name='Notificação de restart diário',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("✅ Sistema de restart automático configurado (4h UTC)")
