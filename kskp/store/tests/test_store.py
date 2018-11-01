import unittest

from kskp.store import PathFileSource

class StoreTestCase(unittest.TestCase):
    def test_path_source(self):
        """
        特定のディレクトリ用のsourceに関するテスト
        """
        source = PathFileSource('kskp/store/tests/frames')
        self.assertEqual(source.data(), [])
