# -*- coding: utf-8 -*-
"""
Script de teste para lembretes
"""
import asyncio
from telegram.ext import Application
from reminders import send_daily_schedule, send_pending_reminder, check_urgent_requests

BOT_TOKEN = "8365753572:AAGiZrUoYxxfYlrRWZaIwNGkKiWQ_EzdX78"

async def test_reminders():
    """Testar todos os lembretes"""
    print("🧪 Testando sistema de lembretes...")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    print("\n1️⃣ Testando resumo diário...")
    await send_daily_schedule(app)
    print("✅ Resumo diário enviado")
    
    await asyncio.sleep(2)
    
    print("\n2️⃣ Testando lembrete de pendentes...")
    await send_pending_reminder(app)
    print("✅ Lembrete de pendentes enviado")
    
    await asyncio.sleep(2)
    
    print("\n3️⃣ Testando verificação de urgentes...")
    await check_urgent_requests(app)
    print("✅ Verificação de urgentes concluída")
    
    print("\n✨ Todos os testes concluídos! Verifique o Telegram.")

if __name__ == '__main__':
    asyncio.run(test_reminders())
