import flask
import flask_sqlalchemy
import flask_restless

from config import config

app = flask.Flask(__name__)
app.config['DEBUG'] = config['debug']


app.config['SQLALCHEMY_DATABASE_URI'] = config['sessions']['db_uri']
db = flask_sqlalchemy.SQLAlchemy(app)

def generate_id():
    from uuid import uuid1
    from hashlib import sha256

    return sha256(uuid1().bytes).hexdigest()

class Session(db.Model):
    __tablename__ = 'session'

    id = db.Column(db.String(64), primary_key=True, default=generate_id)
    user_id = db.Column(db.Integer, nullable=True, default=None)
    last_used_at = db.Column(db.DateTime, nullable=False)
    data_items = db.relationship('SessionDataItem', cascade='all, delete-orphan')

class SessionDataItem(db.Model):
    __tablename__ = 'session_data_item'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), db.ForeignKey('session.id'), nullable=False)
    key = db.Column(db.String, nullable=False)
    value = db.Column(db.PickleType, nullable=False)

db.create_all()


restman = flask_restless.APIManager(app, flask_sqlalchemy_db=db)
restman.create_api(Session,
    collection_name='sessions',
    methods=[
        'GET',
        'POST',
        'PUT',
        'PATCH',
        'DELETE'
    ],
)


if __name__ == '__main__':
    app.run(port=config['sessions']['port'])

