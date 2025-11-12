"""
Funções para guardar estados temporários na base de dados
Substitui context.user_data para garantir persistência entre updates
"""
import json
import sqlite3
from database import get_db

def save_temp_state(user_id: int, state_data: dict):
    """Guardar estado temporário de um utilizador"""
    conn = get_db()
    cursor = conn.cursor()
    
    state_json = json.dumps(state_data)
    
    cursor.execute('''
        INSERT OR REPLACE INTO temp_states (user_id, state_data, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    ''', (user_id, state_json))
    
    conn.commit()
    conn.close()

def get_temp_state(user_id: int) -> dict:
    """Obter estado temporário de um utilizador"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT state_data FROM temp_states WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return json.loads(row[0])
    return {}

def clear_temp_state(user_id: int):
    """Limpar estado temporário de um utilizador"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM temp_states WHERE user_id = ?', (user_id,))
    
    conn.commit()
    conn.close()

def update_temp_state(user_id: int, **kwargs):
    """Atualizar campos específicos do estado temporário"""
    current_state = get_temp_state(user_id)
    current_state.update(kwargs)
    save_temp_state(user_id, current_state)
