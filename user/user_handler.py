from db import Database
from encryption import AESCipher
import logging
import json


class User:
    def __init__(self, email: str):
        self._user_id = None
        self._email = email
        self._pwd = None
        self.cipher = AESCipher()
        self.advisor = 0
        self._logger = logging.getLogger('progress_tracker_api')

    def fetch_or_create_user_login(self, pwd: str):
        if not self._email or not pwd:
            self._logger.error('Missing User name or Password')

            return 0, 'Forbidden -Invalid credentials', 403
        self._pwd = pwd
        exists = self._check_if_user_exists()
        if exists:
            self._user_id = exists
            success, msg = self.fetch_user_login()
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

    def fetch_user_login(self) -> any:
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
            self.advisor, college_id = self.check_if_advisor_user()
            self._user_id = new_id
            if self.advisor:
                sql = """INSERT INTO advisor (id, college_id)
                         VALUES(%s, %s)"""
                with Database() as _db:
                    _db.insert(sql, [new_id, college_id, ])

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

    def check_if_advisor_user(self):
        with open('avisors.json') as f:
            data = json.load(f)
        if data[self._email]:
            college_id = data[self._email]['college_id']
            return 1, college_id
        return 0, None

    def get_user_role(self):
        sql = """SELECT role FROM user WHERE email= %s"""
        with Database() as _db:
            result = _db.select_with_params(sql, [self._email])
        return result[0][0]

    def get_student_details(self, email: str):
        sql = """SELECT id, last_update FROM user WHERE email=%s"""
        with Database() as _db:
            result = _db.select_with_params(sql, [email, ])
        if not result[0][1]:
            return 1, 'first_login', 200

        self._user_id = result[0][0]
        #TODO: Get all the user's data...