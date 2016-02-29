import requests
from datetime import datetime
import simplejson
from urllib.parse import unquote as urldecode

import flask

from config import config
from settings import parse_datetime, render_datetime, \
                 hash_password, \
                 service_uris


app = flask.Flask(__name__)
app.config['DEBUG'] = config['debug']


class Session(dict, flask.sessions.SessionMixin):
    def __init__(self, json):
        self.id = json['id']
        self.user_id = json['user_id']
        self.data = {item['key']: item['value'] for item in json['data_items']}

    @property
    def data(self):
        return self

    @data.setter
    def data(self, data):
        self.clear()
        self.update(data)

    def to_json(self):
        return {
            'user_id': self.user_id,
            'last_used_at': render_datetime(datetime.now()),
            'data_items': [{'key': key, 'value': value} for key, value in self.data.items()]
        }
       
class SessionInterface(flask.sessions.SessionInterface):
    def open_session(self, app, request):
        try:
            if 'session_id' in request.cookies:
                session_response = requests.get(service_uris['sessions'] + '/' + request.cookies['session_id'])
                if session_response.status_code == 200:
                    session = session_response.json()
                    if parse_datetime(session['last_used_at']) + config['website']['session_expires_after'] > datetime.now():
                        return Session(session)

            session_response = requests.post(service_uris['sessions'], json={
                'last_used_at': render_datetime(datetime.now()),
            })
            if session_response.status_code == 201:
                session = session_response.json()
                return Session(session)
        except requests.exceptions.RequestException:
            return Session({
                'id': None,
                'user_id': None,
                'data_items': [],
            })

    def save_session(self, app, session, response):
        if session.id is None:
            response.set_cookie('session_id', '', expires=0)
            return

        try:
            session_response = requests.patch(service_uris['sessions'] + '/' + str(session.id), json=session.to_json())
            if session_response.status_code == 200:
                response.set_cookie('session_id', str(session.id))
        except requests.exceptions.RequestException:
            pass

app.session_interface = SessionInterface()


@app.route('/', methods=['GET'])
def index():
    return flask.redirect('/races/')


@app.route('/register', methods=['GET'])
def register():
    if 'redirect_to' in flask.request.args:
        flask.session['redirect_to'] = urldecode(flask.request.args['redirect_to'])

    if flask.session.user_id is not None:
        return flask.redirect('/me')

    return flask.render_template('register.html')

@app.route('/register', methods=['POST'])
def post_to_register():
    try:
        user_response = requests.post(service_uris['users'], json={
            'login': flask.request.form['login'],
            'password_hash': hash_password(flask.request.form['password']),
            'name': flask.request.form.get('name', None),
            'country': flask.request.form.get('country', None),
            'email': flask.request.form.get('email', None),
        })
    except requests.exceptions.RequestException:
        return flask.render_template('error.html', reason='Users backend is unavailable'), 500

    if user_response.status_code == 201:
        user = user_response.json()
        flask.session.user_id = user['id']
        return flask.redirect(flask.session.pop('redirect_to', '/me'), code=303)

    return flask.render_template('error.html', reason=user_response.json()), 500


@app.route('/sign_in', methods=['GET'])
def sign_in():
    if 'redirect_to' in flask.request.args:
        flask.session['redirect_to'] = urldecode(flask.request.args['redirect_to'])

    if flask.session.user_id is not None:
        return flask.redirect('/me')

    return flask.render_template('sign_in.html')

@app.route('/sign_in', methods=['POST'])
def post_to_sign_in():
    try:
        user_response = requests.get(service_uris['users'], params={
            'q': simplejson.dumps({
                'filters': [
                    {'name': 'login', 'op': '==', 'val': flask.request.form['login']},    
                    {'name': 'password_hash', 'op': '==', 'val': hash_password(flask.request.form['password'])},    
                ],
                'single': True,
            }),
        })
    except requests.exceptions.RequestException:
        return flask.render_template('error.html', reason='Users backend is unavailable'), 500

    if user_response.status_code == 200:
        user = user_response.json()
        flask.session.user_id = user['id']
        return flask.redirect(flask.session.pop('redirect_to', '/me'), code=303)

    return flask.render_template('error.html', reason=user_response.json()), 500


@app.route('/me', methods=['GET'])
def me():
    if flask.session.user_id is None:
        flask.session['redirect_to'] = '/me'
        return flask.redirect('/sign_in')

    try:
        user_response = requests.get(service_uris['users'] + '/' + str(flask.session.user_id))
        assert user_response.status_code == 200
        user = user_response.json()
    except requests.exceptions.RequestException:
        user = None

    return flask.render_template('me.html', user=user)


@app.route('/me', methods=['POST'])
def patch_me():
    user = {}
    if 'password' in flask.request.form and flask.request.form['password']:
        user['password_hash'] = hash_password(flask.request.form['password'])
    if 'name' in flask.request.form:
        user['name'] = flask.request.form['name'] or None
    if 'country' in flask.request.form:
        user['country'] = flask.request.form['country'] or None
    if 'email' in flask.request.form:
        user['email'] = flask.request.form['email'] or None

    try:
        user_response = requests.patch(service_uris['users'] + '/' + str(flask.session.user_id), json=user)
    except requests.exceptions.RequestException:
        return flask.render_template('error.html', reason='Users backend is unavailable'), 500

    if user_response.status_code == 200:
        user = user_response.json()
        return flask.render_template('me.html', user=user)

    return flask.render_template('error.html', reason=user_response.json()), 500


@app.route('/races/', methods=['GET'])
def races():
    user_name = None
    if flask.session.user_id is not None:
        try:
            user_response = requests.get(service_uris['users'] + '/' + str(flask.session.user_id))
            if user_response.status_code != 200:
                return flask.render_template('error.html', reason=user_response.json()), 500

            user = user_response.json()
            user_name = user['name']
        except requests.exceptions.RequestException:
            return flask.render_template('error.html',reason='Users backend is unavailable'), 500

    try:
        per_page = int(flask.request.args.get('per_page', 20))
        page = int(flask.request.args.get('page', 1))

        races_response = requests.get(service_uris['races'], params={
            'results_per_page': per_page,
            'page': page,
        })
        assert races_response.status_code == 200

        races = races_response.json()

        if 'cart' not in flask.session:
            flask.session['cart'] = {}
        for race in races['objects']:
            race['quantity'] = flask.session['cart'].get(str(race['id']), 0)

        pages = races['total_pages']
        page_races = races['objects']
    except requests.exceptions.RequestException:
        pages = 0
        page_races = None

    return flask.render_template('races.html', user_name=user_name,
                                               page_races=page_races,
                                               per_page=per_page,
                                               page=page,
                                               pages=pages)


@app.route('/entry', methods=['GET'])
def entry():
    if flask.session.user_id is None:
        flask.session['redirect_to'] = '/me'
        return flask.redirect('/sign_in')

    race_id = flask.request.args.get('race_id')

    """
    check if this race is already participated
    """
    try:
        entrylist_response = requests.get(service_uris['entrylist'], params={
            'q': simplejson.dumps
            ({
                'filters': [{'name': 'user_id', 'op': '==', 'val': flask.session.user_id},
                            {'name': 'race_id', 'op': '==', 'val': race_id}       
                ],
            }),
        })
        assert entrylist_response.status_code == 200
        entrylist = entrylist_response.json()
        entrylist = entrylist['objects']
        print(entrylist)
    except requests.exceptions.RequestException:
        pass

    if entrylist:
        return flask.render_template('error.html', reason=[{'reason':'already participated this race!'}]), 403
    
   
    races = []
    try:
        race_response = requests.get(service_uris['races'] + '/' + race_id)
        assert race_response.status_code == 200

        c = race_response.json()
        print(c)
        races.append({
            'name': c['name'],
            'country': c['country'],
            'distance': c['distance'],
			'laps': c['laps'],
        })

    except requests.exceptions.RequestException:
        pass

    return flask.render_template('entry.html', races=races)

@app.route('/entry', methods=['POST'])
def post_to_order():

    if flask.session.user_id is None:
        flask.session['redirect_to'] = '/me'
        return flask.redirect('/sign_in')

    race_id = flask.request.args.get('race_id')
    rclass = flask.request.form['rclass']

    try:
        entrylist_response = requests.post(service_uris['entrylist'], json={
            'user_id': flask.session.user_id,
            'race_time': render_datetime(datetime.now()),
            'race_id': race_id,
            'rclass': rclass,
        })
        assert entrylist_response.status_code == 201

    except requests.exceptions.RequestException:
        pass

    print(race_id, ' ', rclass)
    return flask.redirect('/me', code=303)

@app.route('/entrylist/', methods=['GET'])
def entrylist():
    if flask.session.user_id is None:
        flask.session['redirect_to'] = '/entrylist/'
        return flask.redirect('/sign_in')

    user_name = None
    if flask.session.user_id is not None:
        try:
            user_response = requests.get(service_uris['users'] + '/' + str(flask.session.user_id))
            if user_response.status_code != 200:
                return flask.render_template('error.html', reason=user_response.json()), 500

            user = user_response.json()
            user_name = user['name']
        except requests.exceptions.RequestException:
            pass

    try:
        entrylist_response = requests.get(service_uris['entrylist'], params={
            'q': simplejson.dumps({
                'filters': [
                    {'name': 'user_id', 'op': '==', 'val': flask.session.user_id},    
                ],
            }),
        })
        assert entrylist_response.status_code == 200
        entrylist = entrylist_response.json()
        entrylist = entrylist['objects']
    except requests.exceptions.RequestException:
        entrylist = None

    result_entrylist = []

    if entrylist is not None:
        querry = '['
        for entry in entrylist:
            querry += '"' + str(entry['race_id']) + '",'
        querry += ']'
        races_response = requests.get(service_uris['races'], params={
                'q': simplejson.dumps({
                    'filters': [
                        {'name': 'id', 'op': 'in', 'val': querry},
                    ],
                }),
            })
        assert races_response.status_code == 200
        races = races_response.json()
        races = races['objects']

        for entry, race in zip(entrylist,races):
            result_entrylist.append({
                'name': race['name'],
                'country': race['country'],
                'distance': race['distance'],
				'laps': race['laps'],
                'rclass': entry['rclass'],
                })

    return flask.render_template('entrylist.html', user_name=user_name,
                                                entrylist=result_entrylist)


if __name__ == '__main__':
    app.run(port=config['website']['port'])

#data = {'name':,'lector':,'price':'100','location':'department#1'}