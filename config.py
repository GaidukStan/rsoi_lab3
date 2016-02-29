from datetime import timedelta

config = {
    'debug': True,

    'website': {
        'port': 5000,
        'session_expires_after': timedelta(weeks=2),
    },       

    'sessions': {
        'port': 5051,
        'db_uri': 'sqlite:///:memory:',
    },       
    'users': {
        'port': 5052,
        'db_uri': 'sqlite:///db/users',
    }, 
        'races': {
        'port': 5053,
        'db_uri': 'sqlite:///db/races',
    },       
    'entrylist': {
        'port': 5054,
        'db_uri': 'sqlite:///db/entrylist',
    },       
}
