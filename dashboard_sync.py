# -*- coding: utf-8 -*-
"""
Sincronização automática de dados para o dashboard
"""
import subprocess
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def sync_dashboard_data():
    """Sincronizar dados do bot para o dashboard"""
    try:
        logger.info("🔄 Iniciando sincronização com dashboard...")
        
        # Executar script de migração
        result = subprocess.run(
            ['npx', 'tsx', 'migrate-bot-data.mjs'],
            cwd='/home/ubuntu/volante-dashboard',
            capture_output=True,
            text=True,
            timeout=60
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
        lambda context: sync_dashboard_data(),
        interval=300,  # 5 minutos em segundos
        first=10,  # Primeira execução após 10 segundos
        name='dashboard_sync'
    )
    
    logger.info("✅ Sincronização automática do dashboard configurada (a cada 5 minutos)")
