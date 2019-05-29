import unittest
import uuid
import distutils.util
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from permission_trial import app
from flask_mail import Mail, Message
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
import permission_trial.models as models
import permission_trial.profile as profile
db = models.db

# テスト用、実際にメールを飛ばさなくなる
app.config.update(
    MAIL_SUPPRESS_SEND=False
)
email_sender = Mail(app)
CONFIRM_EMAIL = 'flask.mail.testtest@gmail.com'

print('メールを飛ばすテストがある（実際には飛ばしていないが）ので、少し実行に時間かかります')

class PROFILETestCase(unittest.TestCase):
    email1 = 'user1@kskp.io'
    email2 = 'user2@kskp.io'

    def setUp(self):
        db.drop_all()
        db.create_all()
        models.create_user('ユーザ１', self.email1, 'testpass')
        models.create_user('ユーザ2', self.email2, 'testpass2')

    def tearDown(self):
        db.drop_all()
        db.session.commit()

    def test_send_email(self):
        """
        メールの送信テスト
        アドレス更新用メールとアドレス変更のお知らせメールの送信
        """
        # 必要情報
        new_email = 'new@kskp.io'
        test_url = 'テストURL'
        user = models.get_user_by_id(1)

        result_box = None

        # アドレス更新用メールとアドレス変更のお知らせメールの送信
        # テスト実行時、少し時間かかります。
        with app.app_context():
            with email_sender.connect() as conn:
                with email_sender.record_messages() as outbox:
                    profile.notify_change_of_email(conn, user, new_email, test_url)
                    result_box = outbox

        self.assertEqual(len(result_box), 2)

        # result_box[0]が新メールアドレス宛て
        # result_box[1]が旧メールアドレス宛て
        self.assertEqual(result_box[0].recipients[0], new_email)
        self.assertEqual(result_box[1].recipients[0], self.email1)

    def test_update_password(self):
        """
        パスワードの更新のテスト
        """
        new_password = 'newpass'
        right_password = 'testpass'
        success = profile.update_password(1, right_password, new_password)
        user = models.get_user_by_id(1)

        self.assertEqual(success, True)
        self.assertEqual(user.password, new_password)

    def test_update_password_failed(self):
        """
        パスワードの更新テスト
        ただし、更新前のパスワードを間違ってしまい更新失敗
        """
        new_password = 'newpass'
        wrong_password = 'wrongpass'
        success = profile.update_password(1, wrong_password, new_password)
        user = models.get_user_by_id(1)

        self.assertEqual(success, False)
        self.assertEqual(user.password, 'testpass')
