# -*- coding: utf-8 -*-
"""
Script para verificar utilizadores na base de dados
"""

import sqlite3

conn = sqlite3.connect('database/hugo_bot.db')
cursor = conn.cursor()

cursor.execute('SELECT telegram_id, username, is_admin, shop_name FROM users')
users = cursor.fetchall()

print("\n" + "="*60)
print("UTILIZADORES NA BASE DE DADOS")
print("="*60)

for user in users:
    telegram_id, username, is_admin, shop_name = user
    admin_status = "✅ ADMIN" if is_admin else "👤 LOJA"
    print(f"\n{admin_status}")
    print(f"  ID: {telegram_id}")
    print(f"  Username: {username}")
    print(f"  Nome da Loja: {shop_name if shop_name else 'N/A'}")

print("\n" + "="*60)
print(f"Total: {len(users)} utilizadores")
print("="*60 + "\n")

conn.close()
