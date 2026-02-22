import unittest
import nysol.mcmd as nm
from streamcat.depo.std.commands.pcmd import copy_nm

class CommandUtilsTest(unittest.TestCase):
    def test_copy_nysol_module(self):
        """
        copy_nm関数のテストをする
        """
        f = None
        f <<= nm.mnewnumber(a="No.", I="1", S="1", l="5")
        [a, b, c] = copy_nm(f, 3)
        
        self.assertTrue(id(a) == id(b) == id(c))
