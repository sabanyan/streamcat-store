import os
import unittest
import json
import uuid
import pprint

from pathlib import Path

# from kskp.library import Library, FRAME_FOLDER_UUID, CACHE_FOLDER_LABEL
# from kskp.library.from_engine.core import Folder, Frame, Cache

from kskp.store import Library, FRAME_FOLDER_UUID, CACHE_FOLDER_LABEL
from kskp.library.from_engine.core import Folder, Frame, Cache

class LibraryTest(unittest.TestCase):

    def test_save_and_load(self):
        frame_file_path = Path('kskp/data/library/' + str(uuid.uuid4()))
        self.save(frame_file_path)
        new_frame = Library.save_frame(FRAME_FOLDER_UUID, 'テストフレーム', frame_file_path)
        saved_frame = Library.load_frame(new_frame.uuid)
        Library.delete_frame(saved_frame.uuid)

    def test_Folder_save(self):
        folder = Folder(Path('kskp/data/library'))
        my_uuid = folder.issue_uuid()
        folder.save({}, None, str(my_uuid))
        
    def test_Folder_load(self):
        folder = Folder(Path('kskp/data/library'))
        my_uuid = folder.issue_uuid()
        with self.assertRaises(Exception) as e:
            folder.load(my_uuid)

    def test_Frame(self):
        frame = Frame()
        frame.set_uuid = str(uuid.uuid4())
        frame.set_cache_info = {'dir_path':'kskp/data/library/'}
        frame.save()
        
    def test_Cache(self):
        cache = Cache()
        cache.set_uuid = str(uuid.uuid4())
        cache.set_cache_info = {'dir_path':'kskp/data/library/'}
        cache.save()
        
    def save(self, file_path):
        with open(file_path, "w") as f:
            f.write("AAAA")


    # def test_get_root(self):
    #     """
    #     ルートフォルダを取得する
    #     """
    #     root = Library.load_root()
    #     self.assertIsNotNone(root.id)
    #     self.assertIsNotNone(root.parent_id)
    #     self.assertIsNotNone(root.uuid)
    #     self.assertIsNotNone(root.path)
    #     self.assertEqual(root.type, 'folder')
    #     self.assertIsNotNone(root.label, 'ROOT_FOLDER')
    #     self.assertIsNotNone(root.creator)
    #     self.assertIsNotNone(root.modifier)
    #     self.assertIsNotNone(root.created_at)
    #     self.assertIsNotNone(root.modified_at)
        
    # def test_get_folder(self):
    #     root = Library.load_root()

    #     folder = Library.load_folder(root.uuid)

    #     self.assertIsNotNone(folder.id)
    #     self.assertIsNotNone(folder.parent_id)
    #     self.assertIsNotNone(folder.uuid)
    #     self.assertIsNotNone(folder.path)
    #     self.assertEqual(folder.type, 'folder')
    #     self.assertIsNotNone(folder.label, 'ROOT_FOLDER')
    #     self.assertIsNotNone(folder.creator)
    #     self.assertIsNotNone(folder.modifier)
    #     self.assertIsNotNone(folder.created_at)
    #     self.assertIsNotNone(folder.modified_at)

    # def test_get_no_folder(self):
    #     with self.asser

    # def test_save_folder(self):
    #     root = Library.load_root()

    #     folder = Library.save_folder(root.uuid, 'フォルダ')

    #     self.assertIsNotNone(folder.id)
    #     self.assertIsNotNone(folder.parent_id)
    #     self.assertIsNotNone(folder.uuid)
    #     self.assertEqual(folder.path, os.path.join(root.path, folder.label))
    #     self.assertEqual(folder.type, 'folder')
    #     self.assertIsNotNone(folder.label, 'フォルダ')
    #     self.assertIsNotNone(folder.creator)
    #     self.assertIsNotNone(folder.modifier)
    #     self.assertIsNotNone(folder.created_at)
    #     self.assertIsNotNone(folder.modified_at)

    