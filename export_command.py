from telegram import Update
from telegram.ext import ContextTypes
from export_stats import generate_stats_excel
from datetime import datetime
import os

DB_PATH = "database/hugo_bot.db"
ADMIN_IDS = [789741735, 615966323, 228613920]

async def exportar_estatisticas_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /exportar_estatisticas - Exportar estatísticas para Excel (Admin)
    """
    user_id = update.effective_user.id
    
    # Verificar se é admin
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Este comando é apenas para administradores.")
        return
    
    await update.message.reply_text("📊 Gerando relatório Excel... Aguarde.")
    
    try:
        # Gerar Excel
        excel_buffer = generate_stats_excel(DB_PATH)
        
        # Nome do arquivo com data
        filename = f"volante-minho-{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        
        # Enviar arquivo
        await update.message.reply_document(
            document=excel_buffer,
            filename=filename,
            caption=(
                "📊 **Relatório de Estatísticas - Volante Minho**\n\n"
                f"📅 Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}\n\n"
                "O arquivo contém 3 sheets:\n"
                "• **Estatísticas Gerais** - Totais por status, tipo e período\n"
                "• **Top Lojas** - Ranking das 10 lojas com mais pedidos\n"
                "• **Histórico Completo** - Todos os pedidos registados"
            ),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Erro ao gerar relatório:\n{str(e)}"
        )
