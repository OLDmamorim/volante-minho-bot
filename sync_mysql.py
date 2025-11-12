# -*- coding: utf-8 -*-
"""
Sincronização automática entre SQLite (bot) e MySQL (dashboard)
"""
import logging
import mysql.connector
from mysql.connector import Error
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

# Credenciais MySQL do dashboard
MYSQL_URL = "mysql://2rEtBRZHWZUfGJS.e70c7b999727:47S8mmgOSqd5aO7efJQ4@gateway02.us-east-1.prod.aws.tidbcloud.com:4000/ge4nSrQ5EKg9ARYTQ47CYY?ssl={\"rejectUnauthorized\":true}"

def parse_mysql_url(url):
    """Parse MySQL URL para obter credenciais"""
    parsed = urlparse(url)
    return {
        'host': parsed.hostname,
        'port': parsed.port or 3306,
        'user': parsed.username,
        'password': parsed.password,
        'database': parsed.path.lstrip('/').split('?')[0]
    }

def get_mysql_connection():
    """Criar conexão com MySQL"""
    try:
        config = parse_mysql_url(MYSQL_URL)
        connection = mysql.connector.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            ssl_ca=None,
            ssl_verify_cert=True
        )
        return connection
    except Error as e:
        logger.error(f"Erro ao conectar ao MySQL: {e}")
        return None

def sync_user_to_mysql(telegram_id, username, shop_name, is_admin):
    """Sincronizar utilizador para MySQL"""
    try:
        conn = get_mysql_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Verificar se utilizador já existe
        cursor.execute(
            "SELECT id FROM users WHERE telegram_id = %s",
            (str(telegram_id),)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Atualizar
            cursor.execute("""
                UPDATE users 
                SET name = %s, role = %s
                WHERE telegram_id = %s
            """, (shop_name or username, 'admin' if is_admin else 'user', str(telegram_id)))
            logger.info(f"Utilizador {telegram_id} atualizado no MySQL")
        else:
            # Inserir
            cursor.execute("""
                INSERT INTO users (telegram_id, name, role)
                VALUES (%s, %s, %s)
            """, (str(telegram_id), shop_name or username, 'admin' if is_admin else 'user'))
            logger.info(f"Utilizador {telegram_id} criado no MySQL")
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Error as e:
        logger.error(f"Erro ao sincronizar utilizador: {e}")
        return False

def sync_request_to_mysql(request_id, shop_telegram_id, shop_name, request_type, start_date, end_date, period, status, rejection_reason=None, created_at=None):
    """Sincronizar pedido para MySQL"""
    try:
        conn = get_mysql_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Primeiro garantir que o utilizador existe
        sync_user_to_mysql(shop_telegram_id, shop_name, shop_name, False)
        
        # Verificar se pedido já existe
        cursor.execute(
            "SELECT id FROM requests WHERE telegram_request_id = %s",
            (str(request_id),)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Atualizar
            cursor.execute("""
                UPDATE requests 
                SET status = %s, 
                    rejection_reason = %s,
                    updated_at = NOW()
                WHERE telegram_request_id = %s
            """, (status, rejection_reason, str(request_id)))
            logger.info(f"Pedido {request_id} atualizado no MySQL")
        else:
            # Inserir
            cursor.execute("""
                INSERT INTO requests 
                (telegram_request_id, user_telegram_id, store_name, request_type, start_date, end_date, period, status, rejection_reason, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                str(request_id),
                str(shop_telegram_id),
                shop_name,
                request_type,
                start_date,
                end_date,
                period,
                status,
                rejection_reason,
                created_at
            ))
            logger.info(f"Pedido {request_id} criado no MySQL")
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Error as e:
        logger.error(f"Erro ao sincronizar pedido: {e}")
        return False

def delete_request_from_mysql(request_id):
    """Remover pedido do MySQL"""
    try:
        conn = get_mysql_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM requests WHERE telegram_request_id = %s",
            (str(request_id),)
        )
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Pedido {request_id} removido do MySQL")
        return True
        
    except Error as e:
        logger.error(f"Erro ao remover pedido: {e}")
        return False
