import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Mocking all dependencies that might be missing
sys.modules['dotenv'] = MagicMock()
sys.modules['langchain_google_genai'] = MagicMock()
sys.modules['langchain_core'] = MagicMock()
sys.modules['langchain_core.prompts'] = MagicMock()
sys.modules['langchain_core.prompts.ChatPromptTemplate'] = MagicMock()
sys.modules['langchain_core.prompts.MessagesPlaceholder'] = MagicMock()
sys.modules['langchain'] = MagicMock()
sys.modules['langchain.agents'] = MagicMock()
sys.modules['src.bots.agent_tools'] = MagicMock()

import src.bots.agent as agent

class TestAgentFallback(unittest.TestCase):
    @patch('src.bots.agent.ChatGoogleGenerativeAI')
    @patch('src.bots.agent.create_tool_calling_agent')
    @patch('os.environ.get')
    def test_get_agent_executor_fallback_logic(self, mock_env_get, mock_create_agent, mock_llm_class):
        # Setup environment mock
        def env_get(key, default=None):
            if key == "GOOGLE_API_KEY": return "fake_key"
            return default
        mock_env_get.side_effect = env_get

        # Mocking the agents created
        mock_agents = [MagicMock(name=f"agent_{i}") for i in range(5)]
        mock_create_agent.side_effect = mock_agents

        executor = agent.get_agent_executor()

        self.assertIsNotNone(executor)

        # Verify that multiple models were instantiated
        # Unique models: gemini-1.5-flash, gemini-1.5-flash-latest, gemini-1.5-pro, gemini-1.0-pro (4 models)
        self.assertEqual(mock_llm_class.call_count, 4)

        # Verify with_fallbacks was called on the first agent runnable
        mock_agents[0].with_fallbacks.assert_called_once()
        fallbacks = mock_agents[0].with_fallbacks.call_args[0][0]
        self.assertEqual(len(fallbacks), 3) # The other 3 models
        self.assertEqual(fallbacks[0], mock_agents[1])

    @patch('src.bots.agent.ChatGoogleGenerativeAI')
    @patch('src.bots.agent.create_tool_calling_agent')
    @patch('os.environ.get')
    def test_unique_models_logic(self, mock_env_get, mock_create_agent, mock_llm_class):
        def env_get(key, default=None):
            if key == "GEMINI_MODEL_NAME": return "custom-model"
            if key == "GOOGLE_API_KEY": return "fake_key"
            return default
        mock_env_get.side_effect = env_get

        mock_create_agent.side_effect = lambda llm, tools, prompt: MagicMock()

        agent.get_agent_executor()

        called_models = [call.kwargs.get('model') for call in mock_llm_class.call_args_list]
        self.assertEqual(called_models[0], "custom-model")
        self.assertIn("gemini-1.5-flash", called_models)
        # Ensure no duplicates
        self.assertEqual(len(called_models), len(set(called_models)))

if __name__ == '__main__':
    unittest.main()
