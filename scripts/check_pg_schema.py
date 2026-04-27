import asyncio
import os
import sys

# Adicionar o caminho do projeto ao sys.path para permitir importações do src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

from src.bots.db import get_pool

async def check():
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Pegar os nomes das colunas da tabela biometria
            columns = await conn.fetch("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'biometria'
            """)
            print("Colunas em biometria (Postgres):", [c['column_name'] for c in columns])
            
            # Pegar os nomes das colunas da tabela leituras (se houver no postgres)
            columns_leituras = await conn.fetch("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'leituras'
            """)
            print("Colunas em leituras (Postgres):", [c['column_name'] for c in columns_leituras])
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    asyncio.run(check())
