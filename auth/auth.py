import jwt
import json
import logging
import base64
from db import Database
from datetime import datetime, timedelta
from user import User

with open('secret.json') as shh:
    _secret = json.load(shh)
_key = _secret.get('secret_key')


class Auth:
    def __init__(self, email: str):
        self._logger = logging.getLogger("progress_tracker_api")
        self._email = email
        self._user = User(email)
        self._api_user = 'progress_tracker'
        self._api_pwd = 'pRoGr355tr4cK'

    def validate_headers(self, header: str):
        auth_type, auth = header.split(' ')
        auth_val = base64.b64decode(auth.encode('UTF-8')).decode('UTF-8')
        user, pwd = auth_val.split(':')
        if user == self._api_user and pwd == self._api_pwd:
            return 1
        else:
            return 0

    def process_user_login(self, pwd: str):
        if not self._email or not pwd:
            return 0, 'Bad Request: missing email or password', 400
        logged_in, response, code = self._user.login(pwd)

        if not logged_in:
            return 0, response, code
        else:
            return 1, 'success', 200

    def process_user_signup(self, pwd: str, firstname: str, lastname: str):
        if not self._email or not pwd:
            return 0, 'Bad Request: missing email or password', 400
        success, response, code = self._user.sign_up(pwd, firstname, lastname)
        if not success:
            return 0, response, code
        return 1, 'Success', 201
