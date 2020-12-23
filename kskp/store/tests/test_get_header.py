import unittest
import nysol.mcmd as nm

from kskp.store import NysolModule
from kskp.depo.std.commands.pcmd.script import *

class GetHeaderTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass
    
    in_data = [
        ['id','val1','val2','val3'],
        ['0','1','2','3'],
        ['1','2','4','6'],
        ['2','3','6','9']]
    
    def test_always_true(self):
        self.assertEqual(self.in_data[0],
                         ['id','val1','val2','val3'])
    
    def test_pcmd_header_get(self):
        in_mread = nm.mread(i= self.in_data)
        in_obj = NysolModule(in_mread)
        
        cmd = PCommand()
        obj, header = cmd.get_field_names(in_obj)

        self.assertTrue(isinstance(obj, NysolModule))
        # not sure how to assert this?
        print(type(header))
        # self.assertEqual(header,['id','val1','val2','val3'])

