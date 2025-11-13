#!/usr/bin/env python3
"""
Script de migração para adicionar tabela temp_states
"""
import sqlite3
import os

DB_PATH = "database/hugo_bot.db"

def migrate():
    """Criar tabela temp_states se não existir"""
    print(f"🔧 Migrando base de dados: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Base de dados não encontrada: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Verificar se tabela já existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='temp_states'")
    if cursor.fetchone():
        print("ℹ️  Tabela temp_states já existe")
    else:
        print("➕ Criando tabela temp_states...")
        cursor.execute('''
            CREATE TABLE temp_states (
                user_id INTEGER PRIMARY KEY,
                state_data TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        print("✅ Tabela temp_states criada com sucesso!")
    
    conn.close()
    print("✅ Migração concluída!")

if __name__ == "__main__":
    migrate()
