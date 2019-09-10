import os
import unittest
import json
import uuid
import pprint
from kskp.auth import User

class AuthTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_man(self):
        admin_user = User.find_by_email('dev@kskp.io')
        admin_user.save()
        admin_user.delete()


