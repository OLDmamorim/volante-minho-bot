# -*- coding: utf-8 -*-
"""
Sincronização automática de dados para o dashboard
"""
import subprocess
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

async def sync_dashboard_data():
    """Sincronizar dados do bot para o dashboard"""
    try:
        logger.info("🔄 Iniciando sincronização com dashboard...")
        
        # Verificar se o diretório do dashboard existe
        import os
        dashboard_path = '/home/ubuntu/volante-dashboard'
        
        if not os.path.exists(dashboard_path):
            logger.warning(f"⚠️ Diretório do dashboard não encontrado: {dashboard_path}")
            logger.info("ℹ️ Sincronização do dashboard desabilitada")
            return
        
        # Executar script de migração em thread separada para não bloquear o bot
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            subprocess.run,
            ['npx', 'tsx', 'migrate-bot-data.mjs'],
            dashboard_path,
            True,  # capture_output
            True,  # text
            60     # timeout
        )
        
        if result.returncode == 0:
            logger.info("✅ Sincronização com dashboard concluída com sucesso")
        else:
            logger.error(f"❌ Erro na sincronização: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        logger.error("⏱️ Timeout na sincronização com dashboard")
    except Exception as e:
        logger.error(f"❌ Erro ao sincronizar com dashboard: {e}")


def setup_dashboard_sync(app):
    """Configurar sincronização automática a cada 5 minutos"""
    from apscheduler.triggers.interval import IntervalTrigger
    
    # Sincronizar a cada 5 minutos
    app.job_queue.run_repeating(
        sync_dashboard_data,
        interval=300,  # 5 minutos em segundos
        first=10,  # Primeira execução após 10 segundos
        name='dashboard_sync'
    )
    
    logger.info("✅ Sincronização automática do dashboard configurada (a cada 5 minutos)")
