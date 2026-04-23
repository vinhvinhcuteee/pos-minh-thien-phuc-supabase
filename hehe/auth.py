from functools import wraps
from flask import session, redirect, url_for

ADMIN_USERNAME = "hoangvinh"
ADMIN_PASSWORD = "Vohoangvinh0807"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def check_login(username, password):
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD
