from db import Database
from encryption import AESCipher
from auth import Auth
import logging


class User:
    def __init__(self, email: str):
        self._user_id = None
        self._email = email
        self._pwd = None
        self.cipher = AESCipher()
        self._logger = logging.getLogger('progress_tracker_api')

    def fetch_or_create_user(self, pwd: str):
        if not self._email or not pwd:
            self._logger.error('Missing User name or Password')

            return 0, 'Forbidden -Invalid credentials', 403
        self._pwd = pwd
        exists = self._check_if_user_exists()
        if exists:
            self._user_id = exists
            success, msg = self.fetch_user()
        else:
            success, msg = self.create_user()

        if not success:
            return success, 'Forbidden- ' + msg, 403
        return 1, 'success'

    def _check_if_user_exists(self) -> int:
        sql = """SELECT id FROM users WHERE email = %s"""

        with Database() as _db:
            user_id = _db.select_with_params(sql, [self._email, ])
        if user_id:
            return user_id[0][0]
        else:
            return 0

    def fetch_user(self) -> any:
        self._logger.info('Fetching user: ' + self._email)
        with self._db as _db:
            sql = """SELECT password_hash, locked_out
                             FROM login WHERE user_id = %s"""
            result = _db.select_with_params(sql, [self._user_id, ])
        decrypted_pwd = self.cipher.decrypt(result[0][1])

        if decrypted_pwd != self._pwd:
            return 0, 'invalid_password'
        elif result[0][2]:
            return 0, 'locked_out'
        else:
            return 1, 'success'

    def create_user(self):
        self._logger.info('Creating new user: ' + self._email)
        encrypted_pwd = self.cipher.encrypt(self._pwd)

        sql = """INSERT INTO users (email) 
                 VALUES(%s)"""
        with Database() as _db:
            new_id = _db.insert(sql, [self._email, ])
        if new_id:
            self._user_id = new_id
            sql = """INSERT INTO login (user_id, email, pwd_hash)
                     VALUES(%s, %s, %s)"""
            with Database() as _db:
                _db.insert(sql, [new_id, self._email, encrypted_pwd])
            return 1, 'success'
        return 0, 'unable_to_create_user'

    def get_user_id(self):
        return self._user_id

    def get_user_email(self):
        return self._email
