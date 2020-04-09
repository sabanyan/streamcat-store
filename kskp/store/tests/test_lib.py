import os
import unittest
import pprint

from kskp.core import Datum
from kskp.store import Library, STORE_DIR
from kskp.store.factory import Factory, UnAuthzFactory

from .test_case_base import TestCaseBase

class AuthTest(TestCaseBase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @classmethod
    def setUpClass(cls):
        TestCaseBase.setUpClass()
        print('STRT')

    @classmethod
    def tearDownClass(cls):
        TestCaseBase.tearDownClass()
        print('END')


    # @unittest.skip
    def test_readable(self):    
        with UnAuthzFactory() as factory:
            admin_user = factory.find_user_by_email('admin@kskp.io')
            
        with Factory(admin_user) as factory:
            ret = factory.user.find_by_uuid(admin_user.uuid)
            print(ret)

    # @unittest.skip
    def test_library_facade(self):
        # ルートデータストアを取得する
        # root = Library.load_root(self.USER_ID1)
        root = self.factory.data.load_root()
        # 取得したルートデータストアの値を検証する
        self.assertIsNotNone(root.id)
        self.assertIsNone(root.parent_id)
        self.assertIsNotNone(root.uuid)
        self.assertIsNotNone(root.path)
        self.assertEqual(root.type, 'folder')
        self.assertIsNone(root.data)
        self.assertIsNotNone(root.creator)
        self.assertIsNotNone(root.modifier)
        self.assertIsNotNone(root.created_at)
        self.assertIsNotNone(root.modified_at)

    # @unittest.skip
    def test_root(self):
        ret = self.factory.data.find_root()
        print(ret)