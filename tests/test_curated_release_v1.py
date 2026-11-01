import unittest
from aimeton_memory_os.curated_audit import digest

class CuratedReleaseTest(unittest.TestCase):
    def test_stable_hash(self):
        self.assertEqual(digest({'a':1}),digest({'a':1}))
