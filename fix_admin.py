# -*- coding: utf-8 -*-
"""
Script para corrigir registo de administrador na base de dados
"""

import sqlite3

# IDs dos administradores
ADMIN_IDS = [228613920, 615966323]

# Conectar à base de dados
conn = sqlite3.connect('database/hugo_bot.db')
cursor = conn.cursor()

# Atualizar utilizadores para administradores
for admin_id in ADMIN_IDS:
    cursor.execute('''
        UPDATE users 
        SET is_admin = TRUE, shop_name = NULL
        WHERE telegram_id = ?
    ''', (admin_id,))
    print(f"✅ Utilizador {admin_id} atualizado para administrador")

conn.commit()
conn.close()

print("\n🎉 Administradores configurados com sucesso!")
print("Envie /start novamente no Telegram para ver o menu de administrador.")
