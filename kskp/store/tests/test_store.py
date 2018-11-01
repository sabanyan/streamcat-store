import unittest

from kskp.store import PathFileSource

class StoreTestCase(unittest.TestCase):
    def test_path_source(self):
        """
        特定のディレクトリ用のsourceに関するテスト
        """
        source = PathFileSource('frames')
        self.assertEqual(source.data(), [])
