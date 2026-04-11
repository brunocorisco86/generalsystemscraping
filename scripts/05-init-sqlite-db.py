import os
import sqlite3
import sys
from pathlib import Path
from dotenv import load_dotenv

# Adiciona a raiz do projeto ao sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Carrega .env da raiz do projeto
load_dotenv(project_root / ".env")

from src.services.database import SQLITE_DB_PATH

def init_sqlite():
    """Inicializa o banco de dados SQLite local."""
    print(f"--- [05/06] Inicializando banco de dados SQLite em '{SQLITE_DB_PATH}' ---")
    
    os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
    
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        
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
        print("✅ SQLite inicializado com sucesso!")
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao inicializar o SQLite: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_sqlite()
