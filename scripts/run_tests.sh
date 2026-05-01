#!/bin/bash
# Script para facilitar a execução dos testes em ambiente isolado.

# Acessa o diretório raiz do projeto (um nível acima deste script)
cd "$(dirname "$0")/.." || exit 1

echo "=============================================="
echo "Iniciando Suíte de Testes (Ambiente Dummy)"
echo "=============================================="

# Verifica se o ambiente virtual existe. Se sim, tenta ativá-lo.
if [ -d ".venv" ]; then
    echo "[!] Ambiente virtual local detectado, ativando..."
    source .venv/bin/activate
fi

# Verifica se o pytest está instalado
if ! command -v pytest &> /dev/null; then
    echo "❌ Erro: pytest não encontrado."
    echo "Instale as dependências de desenvolvimento executando:"
    echo "pip install -r requirements-dev.txt"
    exit 1
fi

# Executa o pytest
pytest -v

TEST_RESULT=$?

echo "=============================================="
if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ Todos os testes passaram! O ambiente está seguro."
else
    echo "❌ Falha em um ou mais testes! Verifique os logs acima."
fi
echo "=============================================="

exit $TEST_RESULT
