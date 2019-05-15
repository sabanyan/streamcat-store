import unittest
import json
import uuid
import pprint

from pathlib import Path

from kskp.library import Library, FRAME_FOLDER_UUID, CACHE_FOLDER_LABEL
from kskp.library.from_engine.core import Folder, Frame, Cache

class LibraryTest(unittest.TestCase):

    def test_save_and_load(self):
        frame_file_path = Path('kskp/library/tests/' + str(uuid.uuid4()))
        self.save(frame_file_path)
        new_frame = Library.save_frame(FRAME_FOLDER_UUID, 'テストフレーム', frame_file_path)
        saved_frame = Library.load_frame(new_frame.uuid)
        saved_frame.delete()

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
        frame.set_cache_info = {'dir_path':'kskp/library/tests/'}
        frame.save()
        
    def test_Cache(self):
        cache = Cache()
        cache.set_uuid = str(uuid.uuid4())
        cache.set_cache_info = {'dir_path':'kskp/library/tests/'}
        cache.save()
        
    def save(self, file_path):
        with open(file_path, "w") as f:
            f.write("AAAA")
