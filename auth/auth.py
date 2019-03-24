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

    def process_user_login(self, pwd: str):
        if not self._email or not pwd:
            return 0, 'Bad Request: missing email or password', 400
        logged_in, response, code = self._user.login(pwd)

        if  not logged_in:
            return 0, response, code
        token = self._check_if_token_exists(self._email)

        if token:
            success, message, code = self.validate_token(token, self._email)

            if success:
                return 1, token, code
            elif message == 'unauthorized' or message == 'invalid_token':
                return 0, 'Forbidden - user/token mismatch or invalid token', code
            elif message == 'signature_expired':
                return self._refresh_token(token)
        else:
            return self._encode_auth_token(self._email, False)

    def process_user_signup(self, pwd: str):
        if not self._email or not pwd:
            return 0, 'Bad Request: missing email or password', 400
        pwd = base64.decode(pwd)
        success, response, code = self._user.sign_up(pwd)

        if not success:
            return 0, response, code
        return self._encode_auth_token(self._email, False)

    def _refresh_token(self, token):
        self._delete_token(token)
        return self._encode_auth_token(self._email, True)

    def _encode_auth_token(self, email: str, refresh: bool) -> any:
        self._logger.info('Creating new access token for: ' + email)
        try:
            payload = {
                'exp': datetime.utcnow() + timedelta(days=1, seconds=0),
                'iat': datetime.utcnow(),
                'sub': email
            }

            token = jwt.encode(payload, _key, algorithm='HS256')

            if token:
                if not refresh:
                    self._logger.info('Inserting token in database')
                    sql = "INSERT INTO jwt_auth (token, email) VALUES(%s, %s)"
                else:
                    self._logger.info("Refreshing DB token")
                    sql = "UPDATE jwt_auth SET token = ? WHERE email= %s"
                with Database() as _db:
                    _db.execute_sql(sql, [token, email, ])

                return 1, token, 200
            else:
                return 0, 'Unable to create access token', 500

        except Exception as e:
            self._logger.error('ERROR---->unable to create new access token: ' + e)
            return 0, e, 500

    def validate_token(self, token: any, email: str) -> any:
        self._logger.info('Validating access token for: ' + email)
        try:
            payload = jwt.decode(token, _key)
            jwt_email = payload['sub']
            if email != jwt_email:
                self._logger.info('Unauthorized user: ' + email)

                return 0, 'unauthorized', 403

            with Database() as _db:
                sql = 'SELECT email FROM jwt_auth WHERE token = %s'
                result = _db.select_with_params(sql, [token, ])
            if not result:
                self._logger.info('No access token for user: ' + email)
                success = 0
                message = 'no_token_stored'
                code = None
            elif result[0][0] != email:
                self._logger.info('Unauthorized action for user: ' + email)
                message = 'unauthorized'
                code = 403
            else:
                success = 1
                message = 'valid'
                code = 200

            return success, message, code

        except jwt.ExpiredSignatureError:
            self._logger.info('Access token signature expired for user: ' + email)
            return 0, 'signature_expired', 400
        except jwt.InvalidTokenError:
            self._logger.info('Invalid access token for user: ' + email)
            return 0, 'invalid_token', 400

    @staticmethod
    def _delete_token(token: str) -> None:
        sql = "DELETE FROM jwt_auth WHERE token= %s"
        with Database() as _db:
            _db.delete(sql, [token, ])

    @staticmethod
    def _check_if_token_exists(email: str) -> any:
        sql = "SELECT token FROM jwt_auth WHERE email= %s"
        with Database() as _db:
            token = _db.select_with_params(sql, [email, ])

        return token[0][0] if token else None
