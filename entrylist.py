import flask
import flask_sqlalchemy
import flask_restless

from config import config

app = flask.Flask(__name__)
app.config['DEBUG'] = config['debug']


app.config['SQLALCHEMY_DATABASE_URI'] = config['entrylist']['db_uri']
db = flask_sqlalchemy.SQLAlchemy(app)

class Entry(db.Model):
    __tablename__ = 'entrylist'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    race_id = db.Column(db.Integer, nullable=False)
    race_time = db.Column(db.DateTime, nullable=False)
    rclass = db.Column(db.Unicode, nullable=False)

db.create_all()


restman = flask_restless.APIManager(app, flask_sqlalchemy_db=db)
restman.create_api(Entry,
    collection_name='entrylist',
    methods=[
        'GET',
        'POST',
        'PUT',
        'PATCH',
        'DELETE'
    ],
)


if __name__ == '__main__':
    app.run(port=config['entrylist']['port'])

