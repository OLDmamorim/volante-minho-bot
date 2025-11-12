# -*- coding: utf-8 -*-
"""
Sistema de restart automático diário
"""
import logging
from datetime import time
from telegram.ext import Application

logger = logging.getLogger(__name__)


async def daily_restart_notification():
    """Notificar que o restart diário vai acontecer"""
    logger.info("🔄 Restart automático diário agendado para daqui a 5 minutos...")
    # O Railway vai fazer restart automaticamente às 4h via config


def setup_auto_restart(app: Application):
    """Configurar restart automático diário"""
    # Usar o job_queue do próprio bot (que já tem event loop)
    job_queue = app.job_queue
    
    if job_queue:
        # Agendar notificação de restart para 3:55 AM UTC (5 min antes do restart real)
        job_queue.run_daily(
            daily_restart_notification,
            time=time(hour=3, minute=55),
            name='daily_restart_notification'
        )
        logger.info("✅ Sistema de restart automático configurado (4h UTC)")
    else:
        logger.warning("⚠️ Job queue não disponível - restart automático não configurado")
