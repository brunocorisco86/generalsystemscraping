import os
import sqlite3
import sys
from pathlib import Path

# Adiciona a raiz do projeto ao sys.path para permitir importações de src
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.services.database import SQLITE_DB_PATH

def init_db():
    """Inicializa o banco de dados SQLite e cria as tabelas necessárias."""
    print(f"--- [05/05] Inicializando banco de dados SQLite em '{SQLITE_DB_PATH}' ---")
    
    # Garante que o diretório pai exista
    os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
    
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        
        # Criação da tabela de leituras (Schema principal do projeto)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leituras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tanque TEXT,
                oxigenio REAL,
                temperatura REAL,
                timestamp_site TIMESTAMP,
                data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                aeradores_ativos INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Banco de dados e tabela 'leituras' inicializados com sucesso!")
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao inicializar o SQLite: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_db()
