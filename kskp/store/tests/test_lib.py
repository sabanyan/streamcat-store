import unittest
import pprint

from kskp.core import Datum
# from kskp.store import Library, Flow, STORE_DIR, Library

from kskp.store.lib import Lib

class AuthTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_readable(self):
        
        with Lib() as lib:
            root = lib.create_folder(None, 'ROOT_FOLDER')
            root.save()

            ret = lib.find_by_uuid(root.uuid)

