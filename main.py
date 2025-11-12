# -*- coding: utf-8 -*-
"""
Bot de Gestão de Pedidos - Hugo
Sistema de gestão de pedidos de apoio às lojas da zona Minho
"""

import logging
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters
)

from config import *
from database.db_manager import DatabaseManager
from handlers import shop_handlers, admin_handlers, command_handlers

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Inicializar base de dados
db = DatabaseManager(DATABASE_PATH)


async def help_command(update: Update, context):
    """Handler para o comando /help"""
    user_id = update.effective_user.id
    is_admin = user_id in ADMIN_IDS
    
    if is_admin:
        help_text = """
🤖 **Bot de Gestão de Pedidos - Hugo**

**Comandos para Gestores:**
/start - Iniciar o bot
/pendentes - Ver pedidos pendentes
/agenda_semana - Ver agenda da semana
/calendario - Ver calendário de pedidos
/estatisticas - Ver estatísticas completas
/adicionar_gestor - Adicionar novo gestor
/listar_usuarios - Listar todos os utilizadores
/comentar - Adicionar comentário a um pedido
/ver_comentarios - Ver comentários de um pedido
/help - Mostrar esta ajuda
"""
    else:
        help_text = """
🤖 **Bot de Gestão de Pedidos - Hugo**

**Comandos para Lojas:**
/start - Iniciar o bot
/pedido - Criar novo pedido
/calendario - Ver calendário de pedidos
/meus_pedidos - Ver meus pedidos
/minha_loja - Ver informações da minha loja
/help - Mostrar esta ajuda
"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def menu_command(update: Update, context):
    """Handler para o comando /menu"""
    telegram_id = update.effective_user.id
    
    # Verificar se é admin
    if telegram_id in ADMIN_IDS or db.is_admin(telegram_id):
        await show_admin_menu(update, context)
        return ADMIN_MENU
    else:
        await show_shop_menu(update, context)
        return MAIN_MENU


async def error_handler(update: Update, context):
    """Handler para erros"""
    logger.error(f"Erro: {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Ocorreu um erro. Por favor, tente novamente ou contacte o suporte."
        )


async def setup_bot_commands(application: Application):
    """Configura o menu de comandos do bot"""
    # Comandos padrão (para todos)
    default_commands = [
        BotCommand("start", "Iniciar o bot"),
        BotCommand("menu", "Voltar ao menu principal"),
        BotCommand("help", "Mostrar ajuda")
    ]
    
    # Comandos para lojas
    shop_commands = [
        BotCommand("start", "Iniciar o bot"),
        BotCommand("pedido", "Criar novo pedido"),
        BotCommand("calendario", "Ver calendário de pedidos"),
        BotCommand("meus_pedidos", "Ver meus pedidos"),
        BotCommand("minha_loja", "Ver informações da minha loja"),
        BotCommand("help", "Mostrar ajuda")
    ]
    
    # Comandos para administradores
    admin_commands = [
        BotCommand("start", "Iniciar o bot"),
        BotCommand("pendentes", "Ver pedidos pendentes"),
        BotCommand("agenda_semana", "Ver agenda da semana"),
        BotCommand("calendario", "Ver calendário de pedidos"),
        BotCommand("estatisticas", "Ver estatísticas completas"),
        BotCommand("adicionar_gestor", "Adicionar novo gestor"),
        BotCommand("listar_usuarios", "Listar todos os utilizadores"),
        BotCommand("comentar", "Adicionar comentário a um pedido"),
        BotCommand("ver_comentarios", "Ver comentários de um pedido"),
        BotCommand("help", "Mostrar ajuda")
    ]
    
    # Definir comandos para lojas (padrão)
    await application.bot.set_my_commands(shop_commands)
    logger.info("✅ Menu de comandos configurado")
    logger.info("   - Comandos para lojas: /pedido, /calendario, /meus_pedidos, /minha_loja")
    logger.info("   - Comandos para admins: /pendentes, /agenda_semana, /calendario, /estatisticas, etc")


def main():
    """Função principal"""
    
    # Verificar se o token está configurado
    if BOT_TOKEN == 'SEU_TOKEN_AQUI':
        logger.error("❌ Token do bot não configurado! Edite o ficheiro config.py")
        return
    
    if not ADMIN_IDS:
        logger.warning("⚠️ Nenhum ID de administrador configurado! Edite o ficheiro config.py")
    
    # Criar aplicação
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Conversation handler para lojas
    shop_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', lambda u, c: shop_handlers.start_command(u, c, db))
        ],
        states={
            AWAITING_SHOP_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: shop_handlers.receive_shop_name(u, c, db))
            ],
            MAIN_MENU: [
                CallbackQueryHandler(lambda u, c: shop_handlers.new_request_callback(u, c, db), pattern='^shop_new_request$'),
                CallbackQueryHandler(lambda u, c: shop_handlers.my_requests_callback(u, c, db), pattern='^shop_my_requests$'),
                CallbackQueryHandler(lambda u, c: shop_handlers.cancel_callback(u, c, db), pattern='^cancel$')
            ],
            SELECTING_REQUEST_TYPE: [
                CallbackQueryHandler(lambda u, c: shop_handlers.select_request_type(u, c, db), pattern='^request_type_'),
                CallbackQueryHandler(lambda u, c: shop_handlers.cancel_callback(u, c, db), pattern='^cancel$')
            ],
            SELECTING_DATE: [
                CallbackQueryHandler(lambda u, c: shop_handlers.select_date(u, c, db), pattern='^calendar_'),
                CallbackQueryHandler(lambda u, c: shop_handlers.cancel_callback(u, c, db), pattern='^cancel$')
            ],
            SELECTING_PERIOD: [
                CallbackQueryHandler(lambda u, c: shop_handlers.select_period(u, c, db), pattern='^period_'),
                CallbackQueryHandler(lambda u, c: shop_handlers.cancel_callback(u, c, db), pattern='^cancel$')
            ],
            CONFIRMING_REQUEST: [
                CallbackQueryHandler(lambda u, c: shop_handlers.confirm_request(u, c, db), pattern='^confirm_request$'),
                CallbackQueryHandler(lambda u, c: shop_handlers.cancel_callback(u, c, db), pattern='^cancel$')
            ],
            ADMIN_MENU: [
                CallbackQueryHandler(lambda u, c: admin_handlers.pending_requests_callback(u, c, db), pattern='^admin_pending$'),
                CallbackQueryHandler(lambda u, c: admin_handlers.all_requests_callback(u, c, db), pattern='^admin_all_requests$'),
                CallbackQueryHandler(lambda u, c: admin_handlers.view_request_callback(u, c, db), pattern='^view_'),
                CallbackQueryHandler(lambda u, c: admin_handlers.approve_request_callback(u, c, db), pattern='^approve_'),
                CallbackQueryHandler(lambda u, c: admin_handlers.reject_request_callback(u, c, db), pattern='^reject_'),
                CallbackQueryHandler(lambda u, c: admin_handlers.admin_back_callback(u, c, db), pattern='^admin_back$')
            ],
            VIEWING_REQUEST: [
                CallbackQueryHandler(lambda u, c: admin_handlers.approve_request_callback(u, c, db), pattern='^approve_'),
                CallbackQueryHandler(lambda u, c: admin_handlers.reject_request_callback(u, c, db), pattern='^reject_'),
                CallbackQueryHandler(lambda u, c: admin_handlers.pending_requests_callback(u, c, db), pattern='^admin_pending$')
            ],
            ENTERING_REJECTION_REASON: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: admin_handlers.receive_rejection_reason(u, c, db))
            ]
        },
        fallbacks=[
            CommandHandler('start', lambda u, c: shop_handlers.start_command(u, c, db)),
            CommandHandler('help', help_command)
        ],
        allow_reentry=True
    )
    
    # Adicionar handlers
    application.add_handler(shop_conv_handler)
    application.add_handler(CommandHandler('help', help_command))
    
    # Handlers de comandos adicionais
    from handlers import shop_commands
    application.add_handler(CommandHandler('pedido', lambda u, c: shop_commands.pedido_command(u, c, db)))
    application.add_handler(CommandHandler('novo_pedido', lambda u, c: shop_commands.pedido_command(u, c, db)))
    application.add_handler(CommandHandler('calendario', lambda u, c: shop_commands.calendario_command(u, c, db)))
    application.add_handler(CommandHandler('meus_pedidos', lambda u, c: shop_commands.meus_pedidos_command(u, c, db)))
    application.add_handler(CommandHandler('minha_loja', lambda u, c: shop_commands.minha_loja_command(u, c, db)))
    application.add_handler(CommandHandler('pendentes', lambda u, c: command_handlers.pendentes_command(u, c, db)))
    application.add_handler(CommandHandler('todos_pedidos', lambda u, c: command_handlers.todos_pedidos_command(u, c, db)))
    application.add_handler(CommandHandler('estatisticas', lambda u, c: command_handlers.estatisticas_command(u, c, db)))
    application.add_handler(CommandHandler('menu', lambda u, c: command_handlers.menu_command(u, c, db)))
    
    # Handler de erros
    application.add_error_handler(error_handler)
    
    # Configurar menu de comandos
    application.post_init = setup_bot_commands
    
    # Iniciar bot
    logger.info("🤖 Bot iniciado com sucesso!")
    logger.info(f"📊 Base de dados: {DATABASE_PATH}")
    logger.info(f"👥 Administradores: {len(ADMIN_IDS)}")
    
    # Executar bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
