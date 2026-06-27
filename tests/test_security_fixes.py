import unittest
from unittest.mock import patch, MagicMock
import sys

# Mock external dependencies BEFORE they are imported anywhere
mock_pd = MagicMock()
mock_plt = MagicMock()
sys.modules['pandas'] = mock_pd
sys.modules['matplotlib'] = MagicMock()
sys.modules['matplotlib.pyplot'] = mock_plt
sys.modules['dotenv'] = MagicMock()

# Mock internal services
sys.modules['src.services.database'] = MagicMock()
sys.modules['src.services.notification'] = MagicMock()
sys.modules['src.bots.agent'] = MagicMock()

# Now we can import the module to test
import src.reports.bot_query_temp as bot_query_temp
import src.reports.bot_query_ox_7d as bot_query_ox_7d

class TestReportSecurity(unittest.TestCase):
    @patch('src.reports.bot_query_temp.get_sqlite_connection')
    @patch('src.reports.bot_query_temp.send_telegram_photo')
    @patch('src.reports.bot_query_temp.send_telegram_message')
    def test_temp_report_parameterization(self, mock_send_msg, mock_send_photo, mock_get_conn):
        # Setup mocks
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        # Return an empty dataframe to stop execution after the query
        mock_pd.read_sql_query.return_value = MagicMock()
        mock_pd.read_sql_query.return_value.empty = True

        # Call the function
        with patch('sys.argv', ['bot_query_temp.py', '123456']):
            bot_query_temp.get_bot_report()

        # Verify pd.read_sql_query was called with parameterized query
        self.assertTrue(mock_pd.read_sql_query.called)

        # Look for the call to read_sql_query
        # In bot_query_temp.py it is called as pd.read_sql_query(query, conn, params=...)
        found = False
        for call in mock_pd.read_sql_query.call_args_list:
            args, kwargs = call
            query = args[0]
            params = kwargs.get('params')
            if '?' in query and params is not None:
                found = True
                break

        self.assertTrue(found, "pd.read_sql_query should be called with '?' and params")

    @patch('src.reports.bot_query_ox_7d.get_sqlite_connection')
    @patch('src.reports.bot_query_ox_7d.send_telegram_photo')
    @patch('src.reports.bot_query_ox_7d.send_telegram_message')
    def test_ox_7d_report_parameterization(self, mock_send_msg, mock_send_photo, mock_get_conn):
        # Setup mocks
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_pd.read_sql_query.return_value = MagicMock()
        mock_pd.read_sql_query.return_value.empty = True

        # Call the function
        with patch('sys.argv', ['bot_query_ox_7d.py', '123456']):
            bot_query_ox_7d.get_weekly_report()

        # Verify pd.read_sql_query was called with parameterized query
        self.assertTrue(mock_pd.read_sql_query.called)

        found = False
        for call in mock_pd.read_sql_query.call_args_list:
            args, kwargs = call
            query = args[0]
            params = kwargs.get('params')
            if '?' in query and params is not None:
                found = True
                break

        self.assertTrue(found, "pd.read_sql_query (weekly) should be called with '?' and params")

def tearDownModule():
    import sys
    for mod in ['pandas', 'matplotlib', 'matplotlib.pyplot', 'dotenv', 
                'src.services.database', 'src.services.notification', 'src.bots.agent']:
        sys.modules.pop(mod, None)

if __name__ == '__main__':
    unittest.main()
