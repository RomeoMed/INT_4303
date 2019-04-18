from db import Database
from encryption import AESCipher
from datetime import datetime
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

    def update_student_details(self, prog_id: str, advisor: str):
        try:
            advisor_id = self._get_advisor_id(advisor)
            sql = """UPDATE student SET
                        degree_program_id= %s, advisor_id= %s, last_updated= %s 
                      WHERE user_id = %s"""
            student_id = self._fetch_user_id()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with Database() as _db:
                _db.execute_sql(sql, [prog_id, advisor_id, now, student_id])
            return 1
        except:
            return 0

    def _get_advisor_id(self, advisor=None):
        if advisor:
            advisor_email = advisor
        else:
            advisor_email = self._email

        sql = "SELECT user_id FROM user WHERE email= %s"
        with Database() as _db:
            result = _db.select_with_params(sql, [advisor_email, ])

        if result:
            return result[0][0]
        else:
            return None

    def get_current_flowchart(self):
        user_id = self._fetch_user_id()
        degree_prog = self._get_student_degree_prog(user_id)
        success, data, code = self._get_student_progress(user_id, degree_prog)

        return success, data, code

    def _get_student_progress(self, user_id: str, degree_prog: str):
        sql = """
                 select
                    d.course_id,
                    c.course_number,
                    c.course_name,
                    c.credits
                 from degree_req d
                 join course c
                    on d.course_id = c.course_id
                where d.degree_prog_id = %s
                """
        with Database() as _db:
            courses = _db.select_into_list(sql, [degree_prog, ])

            sql = """SELECT
                        s.class_id,
                        s.course_code,
                        s.approved,
                        s.class_status
                      FROM student_sched s
                      WHERE s.user_id = %s;
                    """
            schedule = _db.select_into_list(sql, [user_id, ])

        return_obj = self.process_flowchart_results(courses, schedule)

        return 1, return_obj, 200

    def process_flowchart_results(self, courses: list, schedule: list):
        return_list = []
        tmp_list = []

        for item in schedule:
            tmp_list.append(item[0])

        index = 0
        for course in courses:
            course_id = course[0]
            course_num = course[1]
            course_name = course[2]
            credits = course[3]
            approved = 0
            class_status = 'required'

            if course_id in tmp_list:
                sched_index = 0
                for cls in schedule:
                    if cls and cls[0] == course_id:
                        course_num = cls[1]
                        approved = cls[2]
                        class_status = cls[3]
                        sched_index += 1
                        cls.clear()
                        break

                tmp_list.remove(course_id)
                # del courses[index]

            return_list.append(
                {
                    'course_id': course_id,
                    'course_number': course_num,
                    'credits': credits,
                    'course_name': course_name,
                    'class_status': class_status,
                    'approved': approved
                }
            )

            index += 1

        return return_list

    def _get_student_degree_prog(self, user_id: str):
        sql = """SELECT degree_program_id FROM student
                  WHERE user_id= %s"""

        try:
            with Database() as _db:
                result = _db.select_with_params(sql, [user_id, ])
            if result:
                return result[0][0]
            else:
                return None
        except:
            return None

    def _update_result(self, result: any):
        tmp_list = []
        return_list = []
        for res in result:
            if res[4]:
                if res[4] in tmp_list:
                    course_code = None
                    approved = 0
                    class_status = 'required'
                else:
                    course_code = res[4]
                    tmp_list.append(res[4])
                    approved = 1
                    class_status = res[6] if res[6] else 'complete'
            else:
                course_code = res[4]
                approved = res[5] if res[5] else 0
                class_status = res[6] if res[6] else 'required'
            data_dict = {
                'course_id': res[0],
                'course_number': res[1],
                'course_name': res[2],
                'credits': res[3],
                'course_code': course_code,
                'approved': approved,
                'class_status': class_status
            }
            return_list.append(data_dict)
        return return_list

    def get_all_students(self) -> any:
        advisor_id = self._get_advisor_id()
        sql = """
                SELECT 
                    user.user_id, 
                    user.email 
                FROM student
                JOIN degree_prog 
                    ON degree_prog.degree_prog_id = student.degree_program_id
                JOIN user
                    ON user.user_id = student.user_id
                JOIN advisor
                    ON advisor.college_id = degree_prog.college_id
                WHERE advisor.user_id = %s"""

        with Database() as _db:
            result = _db.select_into_list(sql, [advisor_id, ])

        if result:
            return 1, result, 200
        else:
            return 0, 'Internal Server Error', 500

    def admin_get_student_info(self, student_id: str) -> any:

        return self._get_student_info(student_id)

    def _get_student_info(self, student_id: str) -> any:
        sql = """
                SELECT 
                    u.user_id,
                    u.email,
                    CONCAT(u.first_name, ' ', u.last_name) AS name,
                    d.program_name
                FROM user u
                JOIN student s 
                    ON s.user_id = u.user_id
                JOIN degree_prog d
                    ON s.degree_program_id = d.degree_prog_id
                WHERE u.user_id = %s;
            """
        with Database() as _db:
            user_info = _db.select_into_list(sql, [student_id, ])

        if user_info:
            degree_prog = self._get_student_degree_prog(student_id)
            success, data, code = self._get_student_progress(student_id, degree_prog)

            if success:
                return_object = self._process_student_admin_info(user_info, data)
                response = {
                    'success': success,
                    'return_obj': return_object,
                    'code': code
                }
                return success, response, code
        return 0, 'Internal Server Error', 500

    def _process_student_admin_info(self, student_info: any, data: any) -> any:
        return_obj = {}

        for info in student_info:
            return_obj['user_id'] = info[0]
            return_obj['email'] = info[1]
            return_obj['name'] = info[2]
            return_obj['program'] = info[3]

        return_obj['complete'] = []
        return_obj['required'] = []
        return_obj['waiting_approval'] = []
        return_obj['in_progress'] = []

        for course in data:
            status = course.get('class_status')
            del course['approved']

            if status == 'required':
                return_obj['required'].append(course)
            elif status == 'waiting_approval':
                return_obj['waiting_approval'].append(course)
            elif status == 'in_progress':
                return_obj['in_progress'].append(course)
            else:
                return_obj['complete'].append(course)

        return return_obj

    def update_student_progress(self, data: any) -> any:
        user_id = self._fetch_user_id()
        sql = """SELECT course_number FROM course WHERE course_id=%s"""
        insert_sql = """INSERT INTO student_sched (user_id, class_id, course_code,
                            approved, class_status)
                        VALUES(%s, %s, %s, %s, %s)
                     """
        try:
            with Database() as _db:
                for course in data:
                    course_id = course.get('id')
                    course_name = course.get('value')
                    approved = course.get('approved')
                    status = course.get('status')

                    if course_name is None:
                        result = _db.select_into_list(sql, [course_id, ])
                        course_name = result[0][0]
                    _db.execute_sql(insert_sql, [user_id, course_id, course_name,
                                                 approved, status,])

                response = {
                    'code': 201,
                    'success': 1,
                    'message': 'success'
                }
            return 1, response , 201
        except Exception as e:
            return 0, 'Internal Server Error', 500
