# -*- coding: utf-8 -*-
"""
Script para garantir que o Hugo está registado como admin na inicialização
"""
import sqlite3
import logging

logger = logging.getLogger(__name__)

DB_PATH = "database/hugo_bot.db"

def ensure_hugo_admin():
    """Garantir que o Hugo está registado como admin"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar se Hugo já existe
        cursor.execute("SELECT telegram_id, is_admin FROM users WHERE telegram_id = ?", (615966323,))
        result = cursor.fetchone()
        
        if result:
            # Hugo existe, garantir que é admin
            if not result[1]:  # Se não é admin
                cursor.execute(
                    "UPDATE users SET is_admin = TRUE WHERE telegram_id = ?",
                    (615966323,)
                )
                conn.commit()
                logger.info("✅ Hugo promovido a admin")
            else:
                logger.info("✅ Hugo já é admin")
        else:
            # Hugo não existe, criar como admin
            cursor.execute("""
                INSERT INTO users (telegram_id, username, shop_name, is_admin)
                VALUES (?, ?, ?, TRUE)
            """, (615966323, "Hugorfl", "Hugo Silva"))
            conn.commit()
            logger.info("✅ Hugo adicionado como admin")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao garantir Hugo como admin: {e}")
        return False
