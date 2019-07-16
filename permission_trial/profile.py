import time
import hashlib
import pathlib
from flask_mail import Mail, Message
from flask import Flask, render_template, url_for, redirect, request, session, flash
from .models import get_user_by_id
from . import app, db

CONFIRM_EMAIL = 'flask.mail.testtest@gmail.com'

def notify_change_of_email(connect, user, new_email, url):
    """
    変更用のURLがついたメールと、変更のお知らせメールを送信する
    """

    msg1 = Message(
    '【確認】KSKP用のメールアドレス変更のお知らせ',
    sender=CONFIRM_EMAIL,
    recipients=[new_email]
    )
    msg1.html = f"""
    <p>
      {user.name}様<br>
      登録されているメールアドレスを{user.email}から{new_email}への
      <br>
      変更を完了するには<a href={url}>こちら</a>をクリックして下さい。
    </p>
    """

    # 旧メールアドレスに、変更がありましたメールを送る
    msg2 = Message(
    '【確認】KSKP用のメールアドレス変更のお知らせ',
    sender=CONFIRM_EMAIL,
    recipients=[user.email]
    )
    msg2.html = f"""
    <p>
      {user.name}様<br>
      メールアドレスが{user.email}から{new_email}への変更申請があったことをお知らせ致します。
    </p>
    """

    connect.send(msg1)
    connect.send(msg2)

def update_password(user_id, old_password, new_password):
    """
    新しいパスワードを設定する
    古いパスワードのチェックも。
    """
    user = get_user_by_id(user_id)
    if user.password != old_password:
        return False
    user.password = new_password
    db.session.add(user)
    db.session.commit()
    return True
