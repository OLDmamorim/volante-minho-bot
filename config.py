# -*- coding: utf-8 -*-
"""
Configuração do Bot de Gestão de Pedidos - Hugo
"""

import os

# Token do Bot do Telegram (obter do BotFather)
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8365753572:AAGiZrUoYxxfYlrRWZaIwNGkKiWQ_EzdX78')

# IDs dos administradores (Hugo e você)
# IMPORTANTE: Substituir pelos IDs reais do Telegram
ADMIN_IDS = [
    228613920,  # M@ster™
    615966323,  # Hugo Silva
]

# Configurações de Base de Dados
DATABASE_PATH = 'database/hugo_bot.db'

# Configurações de Calendário
CALENDAR_PERIODS = {
    'Manhã': {'start': '09:00:00', 'end': '13:00:00'},
    'Tarde': {'start': '14:00:00', 'end': '18:00:00'},
    'Todo o dia': {'start': '09:00:00', 'end': '18:00:00'}
}

# Tipos de Pedido
REQUEST_TYPES = ['Apoio', 'Férias', 'Outros']

# Estados de Conversação
(
    AWAITING_SHOP_NAME,
    MAIN_MENU,
    SELECTING_REQUEST_TYPE,
    SELECTING_DATE,
    SELECTING_PERIOD,
    CONFIRMING_REQUEST,
    ADMIN_MENU,
    VIEWING_REQUEST,
    ENTERING_REJECTION_REASON
) = range(9)

# Mensagens do Bot
MESSAGES = {
    'welcome_new': '👋 Bem-vindo ao sistema de gestão de pedidos!\n\nPor favor, indique o nome da sua loja:',
    'welcome_back': '👋 Bem-vindo de volta, {shop_name}!\n\nO que deseja fazer?',
    'welcome_admin': '👋 Bem-vindo, Administrador!\n\nO que deseja fazer?',
    'shop_registered': '✅ Loja "{shop_name}" registada com sucesso!',
    'select_request_type': '📋 Selecione o tipo de pedido:',
    'select_date': '📅 Selecione a data do pedido:',
    'select_period': '🕐 Selecione o período do dia:',
    'confirm_request': '✅ Confirmar pedido?\n\n📋 Tipo: {request_type}\n📅 Data: {date}\n🕐 Período: {period}',
    'request_created': '✅ Pedido criado com sucesso!\n\nOs gestores foram notificados.',
    'request_cancelled': '❌ Pedido cancelado.',
    'new_request_notification': '🔔 Novo pedido de {shop_name}:\n\n📋 Tipo: {request_type}\n📅 Data: {date}\n🕐 Período: {period}',
    'request_approved': '✅ O seu pedido foi aprovado!',
    'request_rejected': '❌ O seu pedido foi rejeitado.\n\nMotivo: {reason}',
    'enter_rejection_reason': '📝 Por favor, indique o motivo da rejeição:',
    'no_pending_requests': 'ℹ️ Não há pedidos pendentes.',
    'invalid_command': '❌ Comando inválido. Use /menu para ver as opções.',
}
