# -*- coding: utf-8 -*-
"""
Error handler para capturar e tratar erros do bot
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import Conflict, NetworkError, TimedOut

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler global de erros"""
    
    # Log do erro
    logger.error(f"Exception while handling an update: {context.error}")
    
    # Tratar erro de conflito
    if isinstance(context.error, Conflict):
        logger.error("⚠️ CONFLITO DETECTADO: Outra instância do bot está a correr!")
        logger.error("O bot vai tentar reconectar automaticamente...")
        # O bot vai fazer retry automático
        return
    
    # Tratar erros de rede
    if isinstance(context.error, (NetworkError, TimedOut)):
        logger.warning(f"⚠️ Erro de rede: {context.error}")
        logger.warning("O bot vai tentar reconectar automaticamente...")
        return
    
    # Para outros erros, logar detalhes
    if update:
        if hasattr(update, 'effective_user') and update.effective_user:
            logger.error(f"Update causou erro - User: {update.effective_user.id}")
        if hasattr(update, 'effective_message') and update.effective_message:
            logger.error(f"Update causou erro - Message: {update.effective_message.text}")
    
    # Logar traceback completo
    logger.exception("Traceback completo:", exc_info=context.error)
