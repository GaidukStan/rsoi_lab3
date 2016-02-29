import flask
import flask_sqlalchemy
import flask_restless

from config import config

app = flask.Flask(__name__)
app.config['DEBUG'] = config['debug']


app.config['SQLALCHEMY_DATABASE_URI'] = config['users']['db_uri']
db = flask_sqlalchemy.SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.Unicode, nullable=False)
    password_hash = db.Column(db.String(64), nullable=False)
    name = db.Column(db.Unicode, nullable=True, default=None)
    country = db.Column(db.Unicode,nullable=True, default=None)
    email = db.Column(db.Unicode, nullable=True, default=None)

db.create_all()


restman = flask_restless.APIManager(app, flask_sqlalchemy_db=db)
restman.create_api(User,
    collection_name='users',
    methods=[
        'GET',
        'POST',
        'PUT',
        'PATCH',
        'DELETE'
    ],
)


if __name__ == '__main__':
    app.run(port=config['users']['port'])

