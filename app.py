import logging
import json
from logging.handlers import RotatingFileHandler
from flask import Flask, request, abort
#from flask_cors import CORS
from auth import Auth
from user import User


logPath = 'logs/api.log'
_logger = logging.getLogger("progress_tracker_api")
_logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(logPath, maxBytes=20971520, backupCount=10)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
_logger.addHandler(handler)

app = Flask(__name__)


@app.route("/progress-tracker/v1/signInGate", methods=['POST'])
def sign_in_gate():
    _logger.info('User Sign in request')

    if not request.is_json:
        _logger.info('ERROR---->Invalid request body')
        abort(400)
    else:
        data = request.get_json()
        user_email = data.get('user_email')
        password = data.get('password')
        authorization = request.headers.get('Authorization')
        success, msg, code = _verify_headers(user_email, authorization)
        auth = Auth(user_email)
        if code >= 400:
            return _process_error_response(success, msg, code)

        success, message, code = auth.process_user_login(password)
        if code >= 400:
            return _process_error_response(success, message, code)
        else:
            result = {
                'success': success,
                'code': code
            }

        resp = _process_response(result, code)

    return resp


@app.route('/progress-tracker/v1/signUpGate', methods=["POST"])
def sign_up_gate():
    _logger.info('User sign up request')
    if not request.is_json:
        _logger.info('ERROR---->Invalid request body')
        abort(400)
    else:
        data = request.get_json()
        user_email = data['user_email']
        password = data['password']
        firstname = data['firstname']
        lastname = data['lastname']
        authorization = request.headers.get('Authorization')
        success, msg, code = _verify_headers(user_email, authorization)

        if not success:
            return _process_error_response(success, msg, code)

        auth = Auth(user_email)
        success, message, code = auth.process_user_signup(password, firstname, lastname)
        print('Success: ' + str(success))
        print('Message: ' + str(message))
        print('Code: ' + str(code))

        if code >= 400:
            return _process_error_response(success, message, code)
        else:
            result = {
                'success': success,
                'code': code
            }

        resp = _process_response(result, code)

    return resp


@app.route("/progress-tracker/v1/getUserRole", methods=['POST'])
def get_user_role():
    if not request.is_json:
        abort(400)

    data = request.get_json()
    user_email = data['user_email']
    authorization = request.headers.get('Authorization')
    success, msg, code = _verify_headers(user_email, authorization)
    if not success:
        return _process_error_response(success, msg, code)
    else:
        user = User(user_email)
        role = user.get_user_role()
        if role == 1:
            role = 'Advisor'
        else:
            role = 'Student'

        result = {
            "user_role": role,
            "code": 200,
            "success": 1
        }
        resp = _process_response(result, 200)

    return resp


@app.route("/progress-tracker/v1/getProgramCourses", methods=["POST"])
def get_program_courses():
    if not request.is_json:
        abort(400)
    else:
        data = request.get_json()
        user_email = data['user_email']
        authorization = request.headers.get('Authorization')
        success, msg, code = _verify_headers(user_email, authorization)
        if code >= 400:
            return _process_error_response(success, msg, code)
        else:
            program = data['major']
            advisor = data['advisor']
            user = User(user_email)
            prog_id = user.get_program_id(program)
            success = user.update_student_details(prog_id, advisor)
            success, course_obj = user.get_all_courses(prog_id)

            if success:
                return _process_response(course_obj, 200)


@app.route("/progress-tracker/v1/getStudentDetails", methods=['POST'])
def get_student_details():
    if not request.is_json:
        abort(400)
    else:
        data = request.get_json()
        user_email = data['user_email']
        authorization = request.headers.get('Authorization')
        success, msg, code = _verify_headers(user_email, authorization)
        if code >= 400:
            return _process_error_response(success, msg, code)
        else:
            user = User(user_email)
            user_details = user.get_student_details()
            print('incomplete')


@app.route('/progress-tracker/v1/check_email_exists/<path:email>', methods=['POST'])
def check_email_exists(email):
    user = User(email)
    authorization = request.headers.get('Authorization')
    success, msg, code = _verify_headers(email, authorization)

    if not success:
        return _process_error_response(success, msg, code)

    exists = user.check_if_user_exists()
    if exists == True:
        response = 1
    else:
        response = 0
    result = {
        "exists": response
    }
    return _process_response(result, 200)


@app.route("/progress-tracker/v1/initialCourseIntake/<path:email>", methods=['POST'])
def initial_course_intake(email):
    user = User(email)
    authorization = request.headers.get('Authorization')
    success, msg, code = _verify_headers(email, authorization)

    if not success:
        return _process_error_response(success, msg, code)
    elif not request.is_json:
        abort(400)
    else:
        data = request.get_json()
        success, msg, code = user.initial_update_schedule(data)

        return _process_response({"success": 1, "message": msg, "code": code}, code)


@app.route('/progress-tracker/v1/getFlowchartData/<path:email>', methods=['POST'])
def get_flowchart_data(email):
    user = User(email)
    authorization = request.headers.get('Authorization')
    success, msg, code = _verify_headers(email, authorization)

    if not success:
        return _process_error_response(success, msg, code)

    success, data, code = user.get_current_flowchart()

    if not success:
        return _process_error_response(success, data, code)
    else:
        return _process_response(data, code)


@app.route("/progress-tracker/v1/getAllStudents/<path:admin>", methods=['POST'])
def get_students(admin):
    user = User(admin)
    authorization = request.headers.get('Authorization')
    success, msg, code = _verify_headers(admin, authorization)
    if not success:
        return _process_error_response(success, msg, code)

    success, students, code = user.get_all_students()
    if not success:
        return _process_error_response(success, students, code)
    else:
        return _process_response(students, code)


@app.route("/progress-tracker/v1/adminGetStudentProgress", methods=['POST'])
def admin_student_progress():
    if not request.is_json:
        abort(400)
    else:
        data = request.get_json()
        student_id = data['student_id']
        advisor = data['advisor']
        authorization = request.headers.get('Authorization')
        success, msg, code = _verify_headers(advisor, authorization)
        if code >= 400:
            return _process_error_response(success, msg, code)
        else:
            user = User(advisor)
            success, msg, code = user.admin_get_student_info(student_id)

            if success:
                return _process_response(msg, code)
            else:
                return _process_error_response(success, msg, code)


@app.route("/progress-tracker/v1/updateStudentProgress/<path:email>", methods=['POST'])
def update_student_progress(email):
    if not request.is_json:
        abort(400)
    else:
        data = request.get_json()
        authorization = request.headers.get('Authorization')
        success, msg, code = _verify_headers(email, authorization)
        if code >= 400:
            return _process_error_response(success, msg, code)
        else:
            user = User(email)
            success, msg, code = user.update_student_progress(data)

            if success:
                return _process_response(msg, code)
            else:
                return _process_error_response(success, msg, code)


@app.route("/progress-tracker/v1/adminUpdateStudentProgress", methods=['POST'])
def admin_update_student_progress():
    if not request.is_json:
        abort(400)
    else:
        data = request.get_json()
        advisor = data['advisor']
        student_id = data['student_id']
        authorization = request.headers.get('Authorization')
        success, msg, code = _verify_headers(advisor, authorization)
        if code >= 400:
            return _process_error_response(success, msg, code)
        else:
            user = User(advisor)
            approved = data['approved']
            denied = data['denied']
            status = data['new_status']

            success, msg, code = user.admin_update_student_info(student_id, approved, denied, status)

            if success:
               return _process_response(msg, code)
            else:
               return _process_error_response(success, msg, code)


def _process_response(result: any, code: int) -> any:
    try:
        resp = app.response_class(
            response=json.dumps(result),
            status=code,
            mimetype='application/json'
        )
        resp.headers['Content-Type'] = 'application/json;charset=UTF-8'

        return resp
    except Exception as e:
        print('Process response error: ' + e)


def _process_error_response(success: int, msg: str, code: int) -> any:
    result = {
        "success": success,
        "code": code,
        "error": msg
    }
    resp = app.response_class(
        response=json.dumps(result),
        status=code,
        mimetype='application/json'
    )
    resp.headers['Content-Type'] = 'application/json;charset=UTF-8'

    return resp


def _verify_headers(user_email: str, authorization: str):
    auth = Auth(user_email)
    success = auth.validate_headers(authorization)
    if success:
        return 1, 'Success', 200
    else:
        return 0, 'Unauthorized: Invalid auth in headers', 400


if __name__ == '__main__':
   # _logger.info('Server is Listening.....')
    app.secret_key = 'f3cfe9ed8fae309f02079dbf'
    app.run(debug=True)
