import unittest
import nysol.mcmd as nm

from kskp.store import NysolModule
from kskp.depo.std.commands.pcmd.script import *

class GetHeaderTestCase(unittest.TestCase):
    def setUp(self):
        self.in_data = [
            ['id','val1','val2','val3'],
            ['0','1','2','3'],
            ['1','2','4','6'],
            ['2','3','6','9']]
        self.in_nysol_obj = NysolModule(nm.mread(i= self.in_data))

    def tearDown(self):
        pass
    
    def test_pcmd_header_get_outputs(self):
        """
        PCommandクラスのget_field_names関数の出力テスト
        """
        cmd = PCommand()
        obj, header = cmd.get_field_names(self.in_nysol_obj)

        # Test that returned obj is correctly a NysolModule object
        self.assertIsInstance(obj, NysolModule, 
                              "Returned object is not NysolModule")

        # Check that NysolModule content is m2tee (read from file)
        M2tee_class = nm.submod.m2tee.Nysol_M2tee
        self.assertIsInstance(obj.content, M2tee_class,
                              "Returned flow is not m2tee")
        
        # check that returned header matches input data
        self.assertEqual(header, self.in_data[0],
                         "Returned header does not match input")

