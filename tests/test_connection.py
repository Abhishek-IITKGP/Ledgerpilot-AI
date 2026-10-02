from app.database.connection import get_connection
import unittest

class TestDatabaseConnection(unittest.TestCase):
    def test_db_connection(self):
        connection = get_connection()
        self.assertIsNotNone(connection)
        connection.close()