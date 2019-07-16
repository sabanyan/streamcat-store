from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template
from hamlish_jinja import HamlishExtension
from werkzeug import ImmutableDict
from flask_admin import Admin

class FlaskWithHamlish(Flask):
    jinja_options = ImmutableDict(extensions=[HamlishExtension])

app = Flask('kskp')
admin = Admin(app, name='microblog', template_mode='bootstrap3')
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://dev:test@0.0.0.0:5432/dev"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.secret_key = 'hogehoge'

CONFIRM_EMAIL = 'flask.mail.testtest@gmail.com'
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USERNAME=CONFIRM_EMAIL,
    MAIL_PASSWORD='@passwd1234',
    MAIL_USE_TLS=False,
    MAIL_USE_SSL=True
)

db = SQLAlchemy(app)
