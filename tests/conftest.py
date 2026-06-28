import os
import pytest

@pytest.fixture(scope="session", autouse=True)
def set_test_environment():
    """
    Garante que o ambiente esteja apontando para testes e injeta PROJECT_ROOT.
    Como pytest-dotenv carrega o .env.test primeiro (veja pytest.ini),
    as variáveis dummy já estarão ativas.
    """
    # Sobrescreve o PROJECT_ROOT para o path real para que os módulos importem corretamente,
    # caso ele não esteja setado ou esteja errado no .env.test.
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    os.environ["PROJECT_ROOT"] = project_root

    # Inicializa o banco SQLite de teste com todas as tabelas necessárias
    import importlib.util
    import sys
    spec = importlib.util.spec_from_file_location("init_sqlite_db", os.path.join(project_root, "scripts/05-init-sqlite-db.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules["init_sqlite_db"] = module
    spec.loader.exec_module(module)
    module.init_sqlite()
    
    yield
    
    # Teardown (opcional): limpar arquivos de teste como sqlite e logs criados.
    test_db = os.path.join(project_root, os.environ.get("SQLITE_DB_PATH", "data/test_dummy_db.sqlite"))
    if os.path.exists(test_db):
        try:
            os.remove(test_db)
        except OSError:
            pass
