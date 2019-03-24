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

    def login(self, pwd: str):
        self._pwd = pwd
        user_id = self._fetch_user_id()
        if not user_id:
            return 0, 'Unauthorized- Invalid username', 401

        self._user_id = user_id
        success, msg = self.fetch_user_login()

        if not success:
            return success, 'Forbidden- ' + msg, 403
        return success, 'success', 200

    def sign_up(self, pwd: str):
        self._pwd = pwd
        exists = self.check_if_user_exists()

        if exists:
            return 0, 'Account already exists for this email', 200

        return self.create_user()

    def _fetch_user_id(self) -> int:
        sql = """SELECT user_id FROM user WHERE email = %s"""

        with Database() as _db:
            user_id = _db.select_with_params(sql, [self._email, ])
        if user_id:
            return user_id[0][0]
        else:
            return 0

    def fetch_user_login(self) -> any:
        self._logger.info('Fetching user login: ' + self._email)
        with Database() as _db:
            sql = """SELECT pwd_hash FROM login WHERE email = %s"""
            result = _db.select_with_params(sql, [self._email, ])

        decrypted_pwd = self.cipher.decrypt(result[0][0])

        if decrypted_pwd != self._pwd:
            return 0, 'invalid_password'
        else:
            return 1, 'success'

    def create_user(self):
        self._logger.info('Creating new user: ' + self._email)
        encrypted_pwd = self.cipher.encrypt(self._pwd)

        sql = """INSERT INTO users (email) 
                 VALUES(%s)"""
        with Database() as _db:
            new_id = _db.execute_sql(sql, [self._email, ])
        if new_id:
            self.advisor, college_id = self.check_if_advisor_user()
            self._user_id = new_id
            if self.advisor:
                sql = """INSERT INTO advisor (id, college_id)
                         VALUES(%s, %s)"""
                params = [new_id, college_id,]
            else:
                sql = """INSERT INTO student (id)
                         VALUES(%s)"""
                params = [new_id,]
            with Database() as _db:
                _db.execute_sql(sql, params)

            sql = """INSERT INTO login (user_id, email, pwd_hash)
                     VALUES(%s, %s, %s)"""
            with Database() as _db:
                _db.execute_sql(sql, [new_id, self._email, encrypted_pwd])

            return 1, 'success', 200

        return 0, 'Internal server error: unable to create user', 500

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
        sql = """SELECT advisor FROM user WHERE email= %s"""
        with Database() as _db:
            result = _db.select_with_params(sql, [self._email])
        return result[0][0]

    def get_student_details(self, email: str):
        first_login = self.is_first_login()

        if first_login:
            return 0, 'details_form', 200
        else:
            return self.get_details()

    def get_details(self):
        #TODO: sql to get details
        return 'stuff'

    def check_if_user_exists(self)-> bool:
        sql = """SELECT id FROM user WHERE email=%s"""
        with Database() as _db:
            result = _db.select_with_params(sql, [self._email, ])
        if result[0][0]:
            return True
        return False

    def is_first_login(self) -> bool:
        sql = """SELECT last_updated FROM student
                 WHERE user_id=%s"""
        with Database() as _db:
            result = _db.select_with_params(sql, [self._user_id, ])
        if result[0][0]:
            return False
        else:
            return True

