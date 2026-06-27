import unittest
from unittest.mock import patch, MagicMock
import sys
# Mock langchain packages
for mod in ['langchain_google_genai', 'langchain_core', 'langchain_core.prompts', 
            'langchain_core.prompts.ChatPromptTemplate', 'langchain_core.prompts.MessagesPlaceholder', 
            'langchain', 'langchain.agents', 'src.bots.agent_tools']:
    sys.modules[mod] = MagicMock()

import pandas as pd
from datetime import datetime

# Importamos o que vamos testar (ou simular)
# Nota: Como ainda não alteramos o feed_prediction.py, vamos focar na lógica de resumo
def format_data_summary_micro(ambient_temp, tanks_data):
    """
    Versão condensada da lógica que iremos implementar no feed_prediction.py
    """
    summary = f"Clima: {ambient_temp:.1f}C. "
    tanks_str = []
    for t in tanks_data:
        tanks_str.append(f"{t['name']}: O2={t['o2']:.1f}, Temp={t['temp']:.1f}C, Trato={t['trato']}")
    return summary + " | ".join(tanks_str)

class TestFeedPredictionAgent(unittest.TestCase):

    def test_data_summary_token_optimization(self):
        """Valida se o resumo de dados é realmente curto (Micro-contexto)."""
        ambient_temp = 28.5
        tanks_data = [
            {'name': 'Tanque 1', 'o2': 3.2, 'temp': 24.1, 'trato': '08:45'},
            {'name': 'Tanque 2', 'o2': 2.9, 'temp': 24.3, 'trato': '09:20'}
        ]
        
        summary = format_data_summary_micro(ambient_temp, tanks_data)
        
        # O resumo deve ser bem curto
        print(f"\nResumo gerado: {summary}")
        self.assertLess(len(summary), 150)
        self.assertIn("Clima: 28.5C", summary)
        self.assertIn("Tanque 1: O2=3.2", summary)

    @patch('src.bots.agent.get_agent_executor')
    def test_analyze_feed_prediction_sync_mock(self, mock_init):
        """Testa a nova função do agente (mockada)."""
        # Mock do LangChain
        mock_executor = MagicMock()
        mock_init.return_value = mock_executor
        mock_executor.invoke.return_value = {"output": "Parecer: Alimentação liberada com cautela devido à temperatura."}
        
        # Simulando a função que vamos criar no agent.py
        from src.bots.agent import analyze_feed_prediction_sync
        
        resumo = "Clima: 30C. T1: O2=3.5, Temp=25C, Trato=08:00"
        resultado = analyze_feed_prediction_sync(resumo)
        
        self.assertIn("Alimentação liberada", resultado)
        self.assertTrue(mock_executor.invoke.called)

def tearDownModule():
    import sys
    for mod in ['langchain_google_genai', 'langchain_core', 'langchain_core.prompts', 
                'langchain_core.prompts.ChatPromptTemplate', 'langchain_core.prompts.MessagesPlaceholder', 
                'langchain', 'langchain.agents', 'src.bots.agent_tools']:
        sys.modules.pop(mod, None)

if __name__ == "__main__":
    unittest.main()
