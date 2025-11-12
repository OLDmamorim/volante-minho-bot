#!/usr/bin/env python3
"""
Volante Minho - Bot do Telegram
Integrado com API do Railway
"""
import os
import logging
import requests
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Configuração
API_URL = "https://volante-dashboard-production.up.railway.app/api/trpc"
BOT_TOKEN = os.getenv("BOT_TOKEN", "8365753572:AAGiZrUoYxxfYlrRWZaIwNGkKiWQ_EzdX78")

# Estados da conversação
TIPO_SERVICO, DATA_INICIO, DATA_FIM, PERIODO, DESCRICAO = range(5)
COMENTARIO_REQ_ID, COMENTARIO_TEXTO = range(5, 7)

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def call_trpc_api(procedure: str, method="GET", data=None):
    """Chama a API tRPC do dashboard"""
    try:
        url = f"{API_URL}/{procedure}"
        
        if method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            response = requests.get(url, timeout=10)
            
        response.raise_for_status()
        response_data = response.json()
        
        # tRPC retorna: {"result": {"data": {"json": [...]}}}
        result = response_data.get("result", {})
        result_data = result.get("data", {})
        
        # Se tiver "json" dentro, retornar isso
        if isinstance(result_data, dict) and "json" in result_data:
            return result_data["json"]
        
        # Senão retornar data diretamente
        return result_data
    except Exception as e:
        logger.error(f"Erro ao chamar API {procedure}: {e}")
        return None


async def get_user_from_telegram(telegram_id: str):
    """Busca utilizador pelo Telegram ID"""
    return call_trpc_api(f"utilizadores.getByTelegramId?input=%7B%22telegramId%22%3A%22{telegram_id}%22%7D")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    welcome_text = """
🚗 **Bem-vindo ao Volante Minho Bot!**

Comandos disponíveis:

📊 **Estatísticas:**
/estatisticas - Ver estatísticas completas
/pendentes - Ver pedidos pendentes

📅 **Agenda:**
/agendasemana - Ver *agenda da semana*
/calendario - Ver *calendário do mês*

👥 **Gestão:**
/adicionargestor - Adicionar novo gestor
/listarusuarios - *Listar utilizadores*

💬 **Comentários:**
/comentar - *Adicionar comentário*
/vercomentarios - Ver comentários de um pedido

Use os comandos para começar!
"""
    await update.message.reply_text(welcome_text, parse_mode='Markdown')


async def estatisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /estatisticas"""
    await update.message.reply_text("📊 A carregar estatísticas...")
    
    # Chamar API
    stats = call_trpc_api("estatisticas.getGeral")
    
    if not stats:
        await update.message.reply_text("❌ Erro ao carregar estatísticas. Tente novamente.")
        return
    
    # Parsear resposta
    total = stats.get("total", 0)
    por_status = stats.get("porStatus", [])
    por_tipo = stats.get("porTipo", [])
    por_loja = stats.get("porLoja", [])
    
    # Contar por status
    pendentes = sum(s["count"] for s in por_status if "PENDENTE" in s["status"])
    aprovados = sum(s["count"] for s in por_status if "APROVADO" in s["status"])
    rejeitados = sum(s["count"] for s in por_status if "REJEITADO" in s["status"])
    
    # Contar por tipo
    ferias = next((t["count"] for t in por_tipo if t["tipo"] == "FERIAS"), 0)
    apoio = next((t["count"] for t in por_tipo if t["tipo"] == "APOIO"), 0)
    outro = next((t["count"] for t in por_tipo if t["tipo"] == "OUTRO"), 0)
    
    # Formatar mensagem
    message = f"""
📊 **Estatísticas Completas**

📋 **Total de Pedidos:** {total}

**Por Status:**
⏳ Pendentes: {pendentes}
✅ Aprovados: {aprovados}
❌ Rejeitados: {rejeitados}

**Por Tipo:**
🏖️ Férias: {ferias}
🚗 Apoio: {apoio}
📋 Outro: {outro}

🔗 Ver dashboard completo:
https://volante-dashboard-production.up.railway.app/
"""
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def pendentes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /pendentes"""
    await update.message.reply_text("⏳ A carregar pedidos pendentes...")
    
    # Chamar API
    pedidos = call_trpc_api("requisicoes.getAll")
    
    if pedidos is None:
        await update.message.reply_text("❌ Erro ao carregar pedidos. Tente novamente.")
        return
    
    # Filtrar pendentes
    pendentes_list = [p for p in pedidos if "PENDENTE" in p.get("requisicao", {}).get("status", "")]
    
    if not pendentes_list:
        await update.message.reply_text("✅ Não há pedidos pendentes!")
        return
    
    # Formatar mensagem
    message = f"⏳ **Pedidos Pendentes ({len(pendentes_list)})**\n\n"
    
    for p in pendentes_list[:10]:  # Limitar a 10
        req = p.get("requisicao", {})
        loja = p.get("loja", {})
        criador = p.get("criador", {})
        
        tipo = req.get("tipoServico", "N/A")
        data_inicio = req.get("dataInicio")
        if data_inicio:
            data_str = datetime.fromisoformat(data_inicio.replace("Z", "+00:00")).strftime("%d/%m/%Y")
        else:
            data_str = "N/A"
        
        message += f"""
🏪 {loja.get("nome", "N/A")} - {tipo}
👤 {criador.get("nome", "N/A")}
📅 {data_str}
---
"""
    
    if len(pendentes_list) > 10:
        message += f"\n... e mais {len(pendentes_list) - 10} pedidos"
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def agenda_semana(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /agenda_semana"""
    await update.message.reply_text("📅 A carregar agenda da semana...")
    
    # Calcular datas
    hoje = datetime.now()
    proxima_semana = hoje + timedelta(days=7)
    
    # Chamar API
    pedidos = call_trpc_api("requisicoes.getAll")
    
    if pedidos is None:
        await update.message.reply_text("❌ Erro ao carregar agenda. Tente novamente.")
        return
    
    # Filtrar pedidos da próxima semana
    agenda = []
    for p in pedidos:
        req = p.get("requisicao", {})
        data_inicio = req.get("dataInicio")
        if data_inicio:
            data = datetime.fromisoformat(data_inicio.replace("Z", "+00:00"))
            if hoje <= data <= proxima_semana:
                agenda.append(p)
    
    if not agenda:
        await update.message.reply_text("✅ Não há pedidos agendados para a próxima semana!")
        return
    
    # Formatar mensagem
    message = f"📅 **Agenda da Semana ({len(agenda)} pedidos)**\n\n"
    
    for p in sorted(agenda, key=lambda x: x.get("requisicao", {}).get("dataInicio", "")):
        req = p.get("requisicao", {})
        loja = p.get("loja", {})
        
        tipo = req.get("tipoServico", "N/A")
        data_inicio = req.get("dataInicio")
        data_str = datetime.fromisoformat(data_inicio.replace("Z", "+00:00")).strftime("%d/%m/%Y")
        periodo = req.get("periodo", "TODO_DIA")
        
        emoji_periodo = "🌅" if periodo == "MANHA" else "🌆" if periodo == "TARDE" else "📆"
        
        message += f"{emoji_periodo} {data_str} - {loja.get('nome', 'N/A')} ({tipo})\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def calendario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /calendario"""
    message = """
📆 **Calendário de Pedidos**

Para ver o calendário visual completo com todos os pedidos do mês, acede ao dashboard:

🔗 https://volante-dashboard-production.up.railway.app/

Lá podes ver:
- 🟢 Dias livres
- 🔵 Dias com pedidos pendentes
- 🔴 Dias ocupados
- 🟡 Pedidos atuais
"""
    await update.message.reply_text(message, parse_mode='Markdown')


async def adicionar_gestor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /adicionar_gestor"""
    await update.message.reply_text("🚧 Funcionalidade em desenvolvimento!\n\nPor agora, adiciona gestores pelo dashboard:\nhttps://volante-dashboard-production.up.railway.app/")


async def listar_usuarios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /listar_usuarios"""
    await update.message.reply_text("👥 A carregar utilizadores...")
    
    # Chamar API
    usuarios = call_trpc_api("utilizadores.getAll")
    
    if usuarios is None:
        await update.message.reply_text("❌ Erro ao carregar utilizadores. Tente novamente.")
        return
    
    if not usuarios:
        await update.message.reply_text("✅ Não há utilizadores registados!")
        return
    
    # Formatar mensagem
    message = f"👥 **Utilizadores ({len(usuarios)})**\n\n"
    
    for u in usuarios[:20]:  # Limitar a 20
        user = u.get("utilizador", {})
        loja = u.get("loja", {})
        
        nome = user.get("nome", "N/A")
        role = user.get("role", "N/A")
        loja_nome = loja.get("nome", "N/A") if loja else "N/A"
        
        emoji_role = "👑" if role == "ADMIN" else "🚗" if role == "VOLANTE" else "🏪"
        
        message += f"{emoji_role} {nome} ({role}) - {loja_nome}\n"
    
    if len(usuarios) > 20:
        message += f"\n... e mais {len(usuarios) - 20} utilizadores"
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def comentar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /comentar"""
    await update.message.reply_text("🚧 Funcionalidade em desenvolvimento!\n\nPor agora, adiciona comentários pelo dashboard:\nhttps://volante-dashboard-production.up.railway.app/")


async def ver_comentarios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /ver_comentarios"""
    await update.message.reply_text("🚧 Funcionalidade em desenvolvimento!\n\nPor agora, vê comentários pelo dashboard:\nhttps://volante-dashboard-production.up.railway.app/")


def main():
    """Inicia o bot"""
    # Criar aplicação
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Adicionar handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("estatisticas", estatisticas))
    application.add_handler(CommandHandler("pendentes", pendentes))
    application.add_handler(CommandHandler("agenda_semana", agenda_semana))
    application.add_handler(CommandHandler("agendasemana", agenda_semana))
    application.add_handler(CommandHandler("calendario", calendario))
    application.add_handler(CommandHandler("adicionar_gestor", adicionar_gestor))
    application.add_handler(CommandHandler("adicionargestor", adicionar_gestor))
    application.add_handler(CommandHandler("listar_usuarios", listar_usuarios))
    application.add_handler(CommandHandler("listarusuarios", listar_usuarios))
    application.add_handler(CommandHandler("comentar", comentar))
    application.add_handler(CommandHandler("ver_comentarios", ver_comentarios))
    application.add_handler(CommandHandler("vercomentarios", ver_comentarios))
    
    # Iniciar bot
    logger.info("Bot iniciado!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
