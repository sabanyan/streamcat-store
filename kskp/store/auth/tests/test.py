import unittest
import pprint

from kskp.core import Datum
# from kskp.store import Library, Flow, STORE_DIR, Library

from kskp.store import ss as session
from kskp.store.auth import User, UserGroup, Group, Auth

class AuthTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @unittest.skip
    def test_man(self):
        pass
        admin_user = User.find_by_email('dev@kskp.io')
        admin_user.save()
        admin_user.delete()

    def test_query(self):
        from kskp.store import Library
        root = Library.load_root(1)

        user1 = User('foo@bar.com', 'passwd', 'foo', 1)
        user1.save()

        group1 = Group('workgroup')
        group1.save()

        usergroup1 = UserGroup(user1.id, group1.id)
        usergroup1.save()

        auth1 = Auth(group1.id, root.id, read=1)
        auth1.save()

        rets = session.query(Datum).filter(Datum.parent_id == None).all()

        print(rets)
        print('readable:', rets[0].readable)


    def test_w_query(self):
        from sqlalchemy.exc import InvalidRequestError

        with self.assertRaises(InvalidRequestError):
            session.query(Datum).filter(Datum.id == 1).delete()
