# -*- coding: utf-8 -*-
"""
Gestor de Base de Dados SQLite
"""

import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
import os


class DatabaseManager:
    """Gestor de base de dados para o bot"""
    
    def __init__(self, db_path: str):
        """
        Inicializa o gestor de base de dados
        
        Args:
            db_path: Caminho para o ficheiro da base de dados
        """
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Obtém uma conexão à base de dados"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Inicializa as tabelas da base de dados"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabela de utilizadores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                is_admin BOOLEAN NOT NULL DEFAULT FALSE,
                shop_name TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de pedidos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shop_telegram_id INTEGER NOT NULL,
                request_type TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE,
                period TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pendente',
                rejection_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                processed_by INTEGER,
                FOREIGN KEY (shop_telegram_id) REFERENCES users (telegram_id),
                FOREIGN KEY (processed_by) REFERENCES users (telegram_id)
            )
        ''')
        
        # Tabela de notificações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER,
                recipient_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (request_id) REFERENCES requests (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # ==================== USERS ====================
    
    def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtém um utilizador pelo ID do Telegram
        
        Args:
            telegram_id: ID do Telegram do utilizador
            
        Returns:
            Dicionário com dados do utilizador ou None
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def create_user(self, telegram_id: int, username: str, is_admin: bool = False, shop_name: str = None) -> bool:
        """
        Cria um novo utilizador
        
        Args:
            telegram_id: ID do Telegram
            username: Nome de utilizador do Telegram
            is_admin: Se é administrador
            shop_name: Nome da loja (se aplicável)
            
        Returns:
            True se criado com sucesso
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (telegram_id, username, is_admin, shop_name)
                VALUES (?, ?, ?, ?)
            ''', (telegram_id, username, is_admin, shop_name))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def update_shop_name(self, telegram_id: int, shop_name: str) -> bool:
        """
        Atualiza o nome da loja de um utilizador
        
        Args:
            telegram_id: ID do Telegram
            shop_name: Novo nome da loja
            
        Returns:
            True se atualizado com sucesso
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET shop_name = ? WHERE telegram_id = ?
        ''', (shop_name, telegram_id))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0
    
    def is_admin(self, telegram_id: int) -> bool:
        """
        Verifica se um utilizador é administrador
        
        Args:
            telegram_id: ID do Telegram
            
        Returns:
            True se for administrador
        """
        user = self.get_user(telegram_id)
        return user and user['is_admin']
    
    # ==================== REQUESTS ====================
    
    def create_request(self, shop_telegram_id: int, request_type: str, 
                      start_date: str, period: str, end_date: str = None) -> Optional[int]:
        """
        Cria um novo pedido
        
        Args:
            shop_telegram_id: ID da loja
            request_type: Tipo de pedido
            start_date: Data de início
            period: Período do dia
            end_date: Data de fim (opcional)
            
        Returns:
            ID do pedido criado ou None
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if end_date is None:
                end_date = start_date
            
            cursor.execute('''
                INSERT INTO requests (shop_telegram_id, request_type, start_date, end_date, period)
                VALUES (?, ?, ?, ?, ?)
            ''', (shop_telegram_id, request_type, start_date, end_date, period))
            
            request_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return request_id
        except Exception as e:
            print(f"Erro ao criar pedido: {e}")
            return None
    
    def get_request(self, request_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtém um pedido pelo ID
        
        Args:
            request_id: ID do pedido
            
        Returns:
            Dicionário com dados do pedido ou None
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.*, u.shop_name 
            FROM requests r
            JOIN users u ON r.shop_telegram_id = u.telegram_id
            WHERE r.id = ?
        ''', (request_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_pending_requests(self) -> List[Dict[str, Any]]:
        """
        Obtém todos os pedidos pendentes
        
        Returns:
            Lista de pedidos pendentes
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.*, u.shop_name 
            FROM requests r
            JOIN users u ON r.shop_telegram_id = u.telegram_id
            WHERE r.status = 'Pendente'
            ORDER BY r.created_at DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_shop_requests(self, telegram_id: int) -> List[Dict[str, Any]]:
        """
        Obtém todos os pedidos de uma loja
        
        Args:
            telegram_id: ID da loja
            
        Returns:
            Lista de pedidos da loja
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM requests 
            WHERE shop_telegram_id = ?
            ORDER BY created_at DESC
        ''', (telegram_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def approve_request(self, request_id: int, admin_id: int) -> bool:
        """
        Aprova um pedido
        
        Args:
            request_id: ID do pedido
            admin_id: ID do administrador
            
        Returns:
            True se aprovado com sucesso
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE requests 
            SET status = 'Aprovado', processed_at = ?, processed_by = ?
            WHERE id = ?
        ''', (datetime.now(), admin_id, request_id))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0
    
    def reject_request(self, request_id: int, admin_id: int, reason: str) -> bool:
        """
        Rejeita um pedido
        
        Args:
            request_id: ID do pedido
            admin_id: ID do administrador
            reason: Motivo da rejeição
            
        Returns:
            True se rejeitado com sucesso
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE requests 
            SET status = 'Rejeitado', processed_at = ?, processed_by = ?, rejection_reason = ?
            WHERE id = ?
        ''', (datetime.now(), admin_id, reason, request_id))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0
    
    # ==================== NOTIFICATIONS ====================
    
    def create_notification(self, recipient_id: int, message: str, request_id: int = None) -> bool:
        """
        Cria uma notificação
        
        Args:
            recipient_id: ID do destinatário
            message: Mensagem da notificação
            request_id: ID do pedido relacionado (opcional)
            
        Returns:
            True se criada com sucesso
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO notifications (recipient_id, message, request_id)
                VALUES (?, ?, ?)
            ''', (recipient_id, message, request_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao criar notificação: {e}")
            return False

    def get_statistics(self):
        """Obter estatísticas dos pedidos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total de pedidos
        cursor.execute('SELECT COUNT(*) FROM requests')
        total = cursor.fetchone()[0]
        
        # Pedidos pendentes
        cursor.execute('SELECT COUNT(*) FROM requests WHERE status = ?', ('Pendente',))
        pending = cursor.fetchone()[0]
        
        # Pedidos aprovados
        cursor.execute('SELECT COUNT(*) FROM requests WHERE status = ?', ('Aprovado',))
        approved = cursor.fetchone()[0]
        
        # Pedidos rejeitados
        cursor.execute('SELECT COUNT(*) FROM requests WHERE status = ?', ('Rejeitado',))
        rejected = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total': total,
            'pending': pending,
            'approved': approved,
            'rejected': rejected
        }
