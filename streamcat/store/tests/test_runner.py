# runner.py
import unittest

# from streamcat.store import StoreModel as Store
# from streamcat.store import FlowData
# from streamcat.store import ProjectFolder
from streamcat.core import Datum
# from .test_lock import LockManagerTest
 
class TestRunner(unittest.TestCase):
 
    def test_runner(self):
        test_suite = unittest.TestSuite()
        # test_suite.addTest(unittest.makeSuite(LockManagerTest))
        unittest.TextTestRunner().run(test_suite)
