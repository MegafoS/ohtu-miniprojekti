import unittest
from initialize_database import initialize_database

class InitDBApp(unittest.TestCase):
        
    def test_app_starts(self):
        initialize_database()

