# runner.py
import unittest

# from kskp.store import StoreModel as Store
# from kskp.store import FlowData
# from kskp.store import ProjectFolder
from kskp.core import Datum
# from .test_lock import LockManagerTest
 
class TestRunner(unittest.TestCase):
 
    def test_runner(self):
        test_suite = unittest.TestSuite()
        # test_suite.addTest(unittest.makeSuite(LockManagerTest))
        unittest.TextTestRunner().run(test_suite)
