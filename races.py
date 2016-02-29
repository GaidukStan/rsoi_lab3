import flask
import flask_sqlalchemy
import flask_restless

from config import config

app = flask.Flask(__name__)
app.config['DEBUG'] = config['debug']


app.config['SQLALCHEMY_DATABASE_URI'] = config['races']['db_uri']
db = flask_sqlalchemy.SQLAlchemy(app)

class Race(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode, nullable=False, unique=True)
    country = db.Column(db.Unicode, nullable=False)
    distance = db.Column(db.Unicode, nullable=False)
    laps = db.Column(db.Unicode, nullable=False)

db.create_all()


restman = flask_restless.APIManager(app, flask_sqlalchemy_db=db)
restman.create_api(Race,
    collection_name='races',
    methods=[
        'GET',
        'POST',
        'PUT',
        'PATCH',
        'DELETE'
    ],
)


if __name__ == '__main__':
    app.run(port=config['races']['port'])

