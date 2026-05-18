import os
import sqlite3
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from src.services.database import get_sqlite_connection

logger = logging.getLogger(__name__)

def init_web_auth_db():
    """Inicializa a tabela de usuários web no SQLite."""
    conn = get_sqlite_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS web_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        
        # Inserir usuário inicial do .env se não existir
        admin_user = os.environ.get("WEB_ADMIN_USER", "admin")
        admin_pass = os.environ.get("WEB_ADMIN_PASS", "admin123")
        
        cursor.execute("SELECT id FROM web_users WHERE username = ?", (admin_user,))
        if not cursor.fetchone():
            logger.info(f"Criando usuário admin padrão: {admin_user}")
            password_hash = generate_password_hash(admin_pass)
            cursor.execute("INSERT INTO web_users (username, password_hash) VALUES (?, ?)", 
                         (admin_user, password_hash))
            conn.commit()
            
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de autenticação web: {e}")
    finally:
        conn.close()

def validate_user(username, password):
    """Valida as credenciais do usuário."""
    conn = get_sqlite_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash FROM web_users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user[2], password):
            return {"id": user[0], "username": user[1]}
        return None
    except Exception as e:
        logger.error(f"Erro ao validar usuário: {e}")
        return None
    finally:
        conn.close()

def get_user_by_id(user_id):
    """Retorna dados do usuário pelo ID."""
    conn = get_sqlite_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM web_users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if user:
            return {"id": user[0], "username": user[1]}
        return None
    except Exception as e:
        logger.error(f"Erro ao buscar usuário por ID: {e}")
        return None
    finally:
        conn.close()
