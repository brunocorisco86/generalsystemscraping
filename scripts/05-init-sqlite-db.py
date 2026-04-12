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

from src.services.database import SQLITE_DB_PATH  # noqa: E402

def init_sqlite():
    """Inicializa o banco de dados SQLite local com o novo MER."""
    print(f"--- [05/06] Inicializando banco de dados SQLite em '{SQLITE_DB_PATH}' ---")
    
    os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
    
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        
        # 1. Tabelas de Cadastro
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS proprietarios (
                uid TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                cpf TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS propriedades (
                uid TEXT PRIMARY KEY,
                proprietario_uid TEXT REFERENCES proprietarios(uid),
                nome TEXT NOT NULL,
                endereco TEXT NOT NULL,
                cadpro TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tipos_exploracao (
                id INTEGER PRIMARY KEY,
                nome TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS estruturas (
                uid TEXT PRIMARY KEY,
                propriedade_uid TEXT REFERENCES propriedades(uid),
                tipo_exploracao_id INTEGER REFERENCES tipos_exploracao(id),
                nome TEXT NOT NULL,
                pluscode TEXT NOT NULL
            )
        ''')

        # 2. Tabelas de Operação e Monitoramento (Principais para o SQLite local)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estrutura_uid TEXT REFERENCES estruturas(uid),
                lote TEXT NOT NULL,
                data_alojamento DATE NOT NULL DEFAULT CURRENT_DATE,
                data_abate DATE,
                peixes_alojados INTEGER,
                peso_medio REAL,
                area_acude REAL,
                densidade REAL,
                qtd_peixes_entregues INTEGER,
                peso_entregue REAL,
                pct_rend_file REAL,
                reais_por_peixe REAL,
                descricao TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leituras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estrutura_uid TEXT REFERENCES estruturas(uid),
                oxigenio REAL,
                temperatura REAL,
                timestamp_site TIMESTAMP,
                data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                aeradores_ativos INTEGER DEFAULT 0
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS biometria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estrutura_uid TEXT REFERENCES estruturas(uid),
                lote TEXT NOT NULL,
                data_biometria DATE NOT NULL,
                volume_peixes INTEGER,
                peso_medio_g REAL,
                consumo_racao_kg REAL
            )
        ''')

        # 3. Tabelas de Qualidade da Água (Específicas)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qualidade_agua_limnologia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estrutura_uid TEXT REFERENCES estruturas(uid),
                data_coleta DATE NOT NULL,
                hora_coleta TIME NOT NULL,
                ph REAL,
                amonia REAL,
                nitrito REAL,
                alcalinidade REAL,
                transparencia REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qualidade_agua_consumo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estrutura_uid TEXT REFERENCES estruturas(uid),
                data_coleta DATE NOT NULL,
                hora_coleta TIME NOT NULL,
                ph REAL,
                sdt REAL,
                orp REAL,
                ppm_cloro REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Popula catálogo de tipos de exploração
        tipos = [
            (1, 'Piscicultura'),
            (2, 'Avicultura'),
            (3, 'Suinocultura'),
            (4, 'Bovinocultura de Leite'),
            (5, 'Bovinocultura de Corte'),
            (6, 'Caprinocultura'),
            (7, 'Ovinocultura')
        ]
        
        for tid, nome in tipos:
            cursor.execute('''
                INSERT OR REPLACE INTO tipos_exploracao (id, nome)
                VALUES (?, ?)
            ''', (tid, nome))

        conn.commit()
        conn.close()
        print("✅ SQLite (Novo MER) inicializado com sucesso!")
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao inicializar o SQLite: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_sqlite()
