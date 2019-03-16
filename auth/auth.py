import jwt
import json
import logging
from db import Database
from datetime import datetime, timedelta
from user import User

with open('secret.json') as shh:
    _secret = json.load(shh)
_key = _secret.get('secret_key')


class Auth:
    def __init__(self, email: str):
        self._logger = logging.getLogger("progress_tracker_api")
        self._user = User(email)

    def process_user(self, pwd: str):
        logged_in, response, code = self._user.fetch_or_create_user_login(pwd)
        if logged_in:
            email = self._user.get_user_email()
            access_token = self._check_if_token_exists(email)

            if access_token:
                success, message, code = self.validate_token(access_token, email)
                if success:
                    return 1, access_token, code
                elif message == 'signature_expired' or message == 'invalid_token':
                    self._delete_token(self, access_token)
                elif message == 'unauthorized':
                    return 0, 'Forbidden - user/token mismatch', code
            new_token = self._encode_auth_token(email)
            if new_token:
                return 1, new_token, 200
            else:
                return 0, 'Unable to create access token', 500
        return logged_in, response, code

    def _encode_auth_token(self, email: str) -> any:
        self._logger.info('Creating new access token for: ' + email)
        try:
            payload = {
                'exp': datetime.utcnow() + timedelta(days=1, seconds=0),
                'iat': datetime.utcnow(),
                'sub': email
            }

            token = jwt.encode(payload, _key, algorithm='HS256')

            if token:
                self._logger.info('Inserting token in database')
                sql = "INSERT INTO jwt_auth (email, token) VALUES(%s, %s)"
                with Database() as _db:
                    _db.insert(sql, [email, token,])

            return token
        except Exception as e:
            self._logger.error('ERROR---->unable to create new access token: ' + e)
            return None

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
            return 0, 'signature_expired.'
        except jwt.InvalidTokenError:
            self._logger.info('Invalid access token for user: ' + email)
            return 0, 'invalid_token.'

    def _delete_token(self, token: str) -> None:
        sql = "DELETE FROM jwt_auth WHERE token= %s"
        with Database() as _db:
            _db.delete(sql, [token, ])

    @staticmethod
    def _check_if_token_exists(email: str) -> any:
        sql = "SELECT token FROM jwt_auth WHERE email= %s"
        with Database() as _db:
            token = _db.select_with_params(sql, [email, ])

        return token[0][0] if token else None
