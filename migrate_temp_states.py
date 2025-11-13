#!/usr/bin/env python3
"""
Script de migração para adicionar tabela temp_states
"""
import sqlite3
import os

DB_PATH = "database/hugo_bot.db"

def migrate():
    """Criar tabela temp_states e adicionar colunas faltantes"""
    print(f"🔧 Migrando base de dados: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Base de dados não encontrada: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Criar tabela temp_states se não existir
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
        print("✅ Tabela temp_states criada!")
    
    # 2. Adicionar colunas faltantes em blocked_dates
    cursor.execute("PRAGMA table_info(blocked_dates)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'blocked_by' not in columns:
        print("➕ Adicionando coluna blocked_by...")
        cursor.execute('ALTER TABLE blocked_dates ADD COLUMN blocked_by INTEGER')
        conn.commit()
        print("✅ Coluna blocked_by adicionada!")
    else:
        print("ℹ️  Coluna blocked_by já existe")
    
    if 'status' not in columns:
        print("➕ Adicionando coluna status...")
        cursor.execute("ALTER TABLE blocked_dates ADD COLUMN status TEXT DEFAULT 'active'")
        conn.commit()
        print("✅ Coluna status adicionada!")
    else:
        print("ℹ️  Coluna status já existe")
    
    if 'temp_id' not in columns:
        print("➕ Adicionando coluna temp_id...")
        cursor.execute('ALTER TABLE blocked_dates ADD COLUMN temp_id INTEGER')
        conn.commit()
        print("✅ Coluna temp_id adicionada!")
    else:
        print("ℹ️  Coluna temp_id já existe")
    
    conn.close()
    print("✅ Migração concluída!")

if __name__ == "__main__":
    migrate()
