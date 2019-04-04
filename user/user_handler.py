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
        try:
            self._pwd = pwd
            user_id = self._fetch_user_id()
            if not user_id:
                return 0, 'Unauthorized- Invalid username', 401

            self._user_id = user_id
            success, msg = self.fetch_user_login()

            if not success:
                return success, 'Forbidden- ' + msg, 403
            return success, 'success', 200
        except Exception as e:
            return 0, 'Internal Server Error: Please Come Back Later', 500

    def sign_up(self, pwd: str, firstname: str, lastname: str):
        self._pwd = pwd
        exists = self.check_if_user_exists()

        if exists:
            return 0, 'Account already exists for this email', 200

        return self.create_user(firstname, lastname)

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

    def create_user(self, firstname: str, lastname: str):
        try:
            with Database() as _db:
                self._logger.info('Creating new user: ' + self._email)
                encrypted_pwd = self.cipher.encrypt(self._pwd)
                self.advisor, college_id = self.check_if_advisor_user()
                advisor_user = 0

                if self.advisor:
                    advisor_user = 1
                sql = """INSERT INTO user (email, advisor, first_name, last_name) 
                        VALUES(%s, %s, %s, %s)"""

                new_id = _db.execute_sql(sql, [self._email, advisor_user, firstname, lastname, ])

                if new_id:
                    self._user_id = new_id

                    if self.advisor:
                        sql = """INSERT INTO advisor (user_id, college_id)
                                VALUES(%s, %s)"""
                        params = [new_id, college_id, ]
                    else:
                        sql = """INSERT INTO student (user_id)
                                VALUES(%s)"""
                        params = [new_id, ]

                    _db.execute_sql(sql, params)

                    sql = """INSERT INTO login (user_id, email, pwd_hash)
                            VALUES(%s, %s, %s)"""
                    _db.execute_sql(sql, [new_id, self._email, encrypted_pwd])

                    return 1, 'success', 200

                return 0, 'Internal server error: unable to create user', 500
        except Exception as e:
            return 0, 'Internal Server Error: Unable to create user', 500

    def get_user_id(self):
        return self._user_id

    def get_user_email(self):
        return self._email

    def check_if_advisor_user(self):
        email = self._email.lower()
        with open('advisors.json') as f:
            data = json.load(f)
        if email in data:
            college_id = data[email]
            return 1, college_id
        return 0, None

    def get_user_role(self):
        sql = """SELECT advisor FROM user WHERE email=%s"""
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
        # TODO: sql to get details
        return 'stuff'

    def check_if_user_exists(self) -> bool:
        sql = """SELECT user_id FROM user WHERE email=%s"""
        with Database() as _db:
            result = _db.select_with_params(sql, [self._email, ])
        if result:
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

    def get_program_id(self, degree: str):
        sql = "SELECT degree_prog_id FROM degree_prog WHERE program_code=%s"
        with Database() as _db:
            prog_id = _db.select_with_params(sql, [degree, ])
        return prog_id[0][0]

    def get_all_courses(self, program_id: str):
        sql = """SELECT c.course_id,
                    c.course_number,
                    c.course_name
                 FROM degree_req dr
                    JOIN course c
                        ON c.course_id = dr.course_id
                 WHERE dr.degree_prog_id = %s;"""
        with Database() as _db:
            result = _db.select_with_params(sql, [program_id, ])
        return_obj = []
        if result:
            for res in result:
                tmp_obj = {
                    "course_id": res[0],
                    "course_number": res[1],
                    "course_name": res[2]
                }
                return_obj.append(tmp_obj)
            return 1, return_obj

    def initial_update_schedule(self, data: any):
        try:
            user_id = self._fetch_user_id()

            sql = """INSERT INTO student_sched (user_id, class_id, course_code,
                        approved, class_status)
                     VALUES(%s,%s,%s,%s,%s)"""

            with Database() as _db:
                for item in data:
                    class_id = item.get('course_id')
                    course_code = item.get('value')
                    approval_status = 1
                    class_status = 'complete'

                    _db.execute_sql(sql, [user_id, class_id, course_code,
                                          approval_status, class_status, ])

            return 1, 'Success', 201
        except:
            return 0, 'Internal Server Error', 500
