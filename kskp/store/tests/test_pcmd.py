import unittest
import nysol.mcmd as nm

from kskp.store import NysolModule
from kskp.depo.std.commands.pcmd.script import *

class PCommandTestCase(unittest.TestCase):
    def setUp(self):
        self.in_data = [
            ['id','val1','val2','val3'],
            ['0','1','2','3'],
            ['1','2','4','6'],
            ['2','3','6','9']]
        self.in_nysol_obj = NysolModule(nm.mread(i= self.in_data))

    def tearDown(self):
        pass

class MultiMcalWCTestCase(PCommandTestCase):
    def perform_without_mcmd(self, args):
        """
        perform multi_mcal_oneformula without using mcmd
        (ideal result)
        """
        _out = []

        return _out
    
    def run_command(self, args):
        """
        Runs MCMD on the input data, using args
        returns output in list form
        """
        cmd = MultiMcalWCCommand()
        result = cmd.run(args = args, inputs = {'i' : self.in_nysol_obj})
        
        return [line for line in result['o'].content.getline(header = True)]

    def test_wildcard_qmark(self):
        """
        Test for question mark wildcard usage
        """
        _args = {
            'targets' : 'val?',
            'a' : 'new_&',
            'c' : '${&}'
        }

        _expected = [
            ['id','val1','val2','val3', 'new_val1', 'new_val2', 'new_val3'],
            ['0','1','2','3','1','2','3'],
            ['1','2','4','6','2','4','6'],
            ['2','3','6','9','3','6','9']
            ]
            
        # in the future, this should be
        # _expected = perform_without_mcmd(_args)
        
        out_list = self.run_command(_args)

        self.assertEqual(_expected, out_list)

    def test_wildcard_aster(self):
        """
        Test for asterisk wildcard usage
        """
        _args = {
            'targets' : 'val*',
            'a' : 'new_&',
            'c' : '${&}'
        }

        _expected = [
            ['id','val1','val2','val3', 'new_val1', 'new_val2', 'new_val3'],
            ['0','1','2','3','1','2','3'],
            ['1','2','4','6','2','4','6'],
            ['2','3','6','9','3','6','9']
            ]
            
        # in the future, this should be
        # _expected = perform_without_mcmd(_args)
        
        out_list = self.run_command(_args)

        self.assertEqual(_expected, out_list)

    def test_commas(self):
        """
        Test for comma target
        """
        _args = {
            'targets' : 'val1,val2,val3',
            'a' : 'new_&',
            'c' : '${&}'
        }

        _expected = [
            ['id','val1','val2','val3', 'new_val1', 'new_val2', 'new_val3'],
            ['0','1','2','3','1','2','3'],
            ['1','2','4','6','2','4','6'],
            ['2','3','6','9','3','6','9']
            ]
            
        # in the future, this should be
        # _expected = perform_without_mcmd(_args)
        
        out_list = self.run_command(_args)

        self.assertEqual(_expected, out_list)
