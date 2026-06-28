import unittest
from unittest.mock import patch, MagicMock
import os
import sys

import src.bots.agent as agent

class TestAgentFallback(unittest.TestCase):
    def test_get_agent_executor_fallback_logic(self):
        with patch('os.environ.get') as mock_env_get, \
             patch('src.bots.agent.ChatGoogleGenerativeAI') as mock_llm_class, \
             patch('src.bots.agent.create_tool_calling_agent') as mock_create_agent, \
             patch('src.bots.agent.AgentExecutor') as mock_agent_executor:
             
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
            self.assertEqual(mock_llm_class.call_count, 4)

            # Verify with_fallbacks was called on the first agent runnable
            mock_agents[0].with_fallbacks.assert_called_once()
            fallbacks = mock_agents[0].with_fallbacks.call_args[0][0]
            self.assertEqual(len(fallbacks), 3) # The other 3 models
            self.assertEqual(fallbacks[0], mock_agents[1])

    def test_unique_models_logic(self):
        with patch('os.environ.get') as mock_env_get, \
             patch('src.bots.agent.ChatGoogleGenerativeAI') as mock_llm_class, \
             patch('src.bots.agent.create_tool_calling_agent') as mock_create_agent, \
             patch('src.bots.agent.AgentExecutor') as mock_agent_executor:

            def env_get(key, default=None):
                if key == "GEMINI_MODEL_NAME": return "custom-model"
                if key == "GOOGLE_API_KEY": return "fake_key"
                return default
            mock_env_get.side_effect = env_get

            mock_create_agent.side_effect = lambda llm, tools, prompt: MagicMock()

            print("AGENT CHAT LLM CLASS:", agent.ChatGoogleGenerativeAI)
            print("MOCK LLM CLASS:", mock_llm_class)

            agent.get_agent_executor()

            called_models = [call.kwargs.get('model') for call in mock_llm_class.call_args_list]
            self.assertEqual(called_models[0], "custom-model")
            self.assertIn("gemini-flash-latest", called_models)
            # Ensure no duplicates
            self.assertEqual(len(called_models), len(set(called_models)))

if __name__ == '__main__':
    unittest.main()
