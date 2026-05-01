import os
from dotenv import load_dotenv

def test_environment_is_isolated():
    """
    Verifica se o pytest está carregando as variáveis dummy do .env.test
    e não vazando as variáveis reais de produção do .env.
    """
    # A variável TELEGRAM_BOT_TOKEN deve ser a string que colocamos no .env.test
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    assert token == "1234567890:TEST_DUMMY_TOKEN_ABCDEFGHIJKLMNOPQRST", \
        f"Alerta de vazamento de ambiente! Token carregado: {token}"

    # Verifica se a IA também está carregando a chave dummy
    gemini_key = os.environ.get("GOOGLE_API_KEY")
    assert gemini_key == "DUMMY_API_KEY_GEMINI_12345", \
        f"Alerta de vazamento! Chave do Gemini carregada: {gemini_key}"

    # Verifica o banco de dados
    sqlite_path = os.environ.get("SQLITE_DB_PATH")
    assert sqlite_path == "data/test_dummy_db.sqlite", \
        f"Alerta de vazamento de banco! Banco apontado: {sqlite_path}"
