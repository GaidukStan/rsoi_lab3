from config import config


def hash_password(password):
    from hashlib import sha256

    return sha256(password.encode('UTF-8')).hexdigest()


time_format = "%Y-%m-%dT%H:%M:%S.%f"

def render_datetime(datetime):
    if datetime is None:
        return None
    return datetime.strftime(time_format)

def parse_datetime(datetime_string):
    from datetime import datetime

    if datetime_string is None:
        return None
    return datetime.strptime(datetime_string, time_format)


service_uris = {service: 'http://localhost:{}/api/{}'.format(config[service]['port'], service) for service in [
    'sessions',
    'users',
    'entrylist',
    'races',
]}

